from __future__ import annotations

import json
import unittest
from urllib.error import URLError

from scripts.topic_radar_client import (
    TopicRadarClient,
    TopicRadarError,
    TopicRadarProtocolError,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def sample_feed(*, items=None):
    return {
        "generated_at": "2026-08-09T00:00:00Z",
        "status": "ok",
        "partial": False,
        "stale": False,
        "items": [] if items is None else items,
        "source_status": [],
    }


class TopicRadarClientTests(unittest.TestCase):
    def test_feed_builds_existing_public_filters_without_business_logic(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(sample_feed())

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        result = client.feed(
            category="technology",
            signal="early_opportunity",
            new_only=True,
            max_age_hours=24,
            min_score=60,
            limit=12,
        )

        self.assertFalse(result["stale"])
        request, timeout = calls[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("/api/v1/ai/topic-radar/feed?", request.full_url)
        self.assertIn("category=technology", request.full_url)
        self.assertIn("signal=early_opportunity", request.full_url)
        self.assertIn("new_only=true", request.full_url)
        self.assertIn("max_age_hours=24", request.full_url)
        self.assertIn("min_score=60", request.full_url)
        self.assertIn("limit=12", request.full_url)
        self.assertEqual(timeout, 15.0)

    def test_feed_requires_stable_item_id_not_topic_id_alias(self) -> None:
        good = sample_feed(items=[{"id": "topic:abc"}])
        bad = sample_feed(items=[{"topic_id": "topic:abc"}])

        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(good),
        )
        self.assertEqual(client.feed()["items"][0]["id"], "topic:abc")

        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(bad),
        )
        with self.assertRaisesRegex(TopicRadarProtocolError, "stable string field 'id'"):
            client.feed()

    def test_insight_posts_only_topic_id_and_locale(self) -> None:
        calls = []

        payload = {
            "topic_id": "topic-1",
            "verdict": "值得研究",
            "angles": [{}, {}, {}],
            "short_video_handoff": {},
        }

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(payload)

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        result = client.insight("topic-1", locale="zh")

        request, timeout = calls[0]
        self.assertEqual(result["topic_id"], "topic-1")
        self.assertEqual(request.get_method(), "POST")
        self.assertTrue(request.full_url.endswith("/insight?locale=zh"))
        self.assertEqual(json.loads(request.data.decode("utf-8")), {"topic_id": "topic-1"})
        self.assertEqual(timeout, 90.0)

    def test_insight_timeout_is_independent_from_read_timeout(self) -> None:
        calls = []
        responses = iter(
            [
                sample_feed(),
                {
                    "topic_id": "topic-1",
                    "verdict": "值得研究",
                    "angles": [{}, {}, {}],
                    "short_video_handoff": {},
                },
            ]
        )

        def opener(request, timeout):
            calls.append(timeout)
            return FakeResponse(next(responses))

        client = TopicRadarClient(
            base_url="https://example.test",
            timeout=4,
            insight_timeout=71,
            opener=opener,
        )
        client.feed()
        client.insight("topic-1")

        self.assertEqual(calls, [4.0, 71.0])
        with self.assertRaisesRegex(ValueError, "insight_timeout"):
            TopicRadarClient(base_url="https://example.test", insight_timeout=0)

    def test_history_requires_expected_contract(self) -> None:
        def opener(request, timeout):
            return FakeResponse({"topic_id": "topic-1", "points": []})

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        self.assertEqual(client.history("topic-1")["points"], [])

    def test_history_and_insight_reject_topic_identity_mismatch(self) -> None:
        responses = iter(
            [
                {"topic_id": "topic-2", "points": []},
                {
                    "topic_id": "topic-2",
                    "verdict": "x",
                    "angles": [],
                    "short_video_handoff": {},
                },
            ]
        )

        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(next(responses)),
        )
        with self.assertRaisesRegex(TopicRadarProtocolError, "does not match"):
            client.history("topic-1")
        with self.assertRaisesRegex(TopicRadarProtocolError, "does not match"):
            client.insight("topic-1")

    def test_feed_rejects_malformed_payload(self) -> None:
        def opener(request, timeout):
            return FakeResponse({"items": []})

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        with self.assertRaises(TopicRadarProtocolError):
            client.feed()

    def test_network_error_is_normalized(self) -> None:
        def opener(request, timeout):
            raise URLError("offline")

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        with self.assertRaisesRegex(TopicRadarError, "offline"):
            client.sources()

    def test_rejects_invalid_signal_and_locale(self) -> None:
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(sample_feed()),
        )
        with self.assertRaises(ValueError):
            client.feed(signal="invented")
        with self.assertRaises(ValueError):
            client.insight("topic-1", locale="fr")


if __name__ == "__main__":
    unittest.main()
