from __future__ import annotations

import contextlib
import json
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

from scripts.topic_radar_client import (
    TopicRadarClient,
    TopicRadarError,
    TopicRadarProtocolError,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "topic_radar_client.py"


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
            q="AI",
            platform="youtube",
            target_platform="douyin",
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
        self.assertIsNone(request.data)
        self.assertIn("/api/v1/ai/topic-radar/feed?", request.full_url)
        self.assertIn("q=AI", request.full_url)
        self.assertIn("category=technology", request.full_url)
        self.assertIn("platform=youtube", request.full_url)
        self.assertIn("target_platform=douyin", request.full_url)
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

    def test_history_requires_expected_contract_and_identity(self) -> None:
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(
                {"topic_id": "topic-1", "points": []}
            ),
        )
        self.assertEqual(client.history("topic-1")["points"], [])

        mismatch = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(
                {"topic_id": "topic-2", "points": []}
            ),
        )
        with self.assertRaisesRegex(TopicRadarProtocolError, "does not match"):
            mismatch.history("topic-1")

    def test_nested_source_and_history_contracts_are_validated(self) -> None:
        bad_source = sample_feed()
        bad_source["source_status"] = [{"id": "x"}]
        with self.assertRaisesRegex(TopicRadarProtocolError, "source_status item"):
            TopicRadarClient(base_url="https://example.test", opener=lambda *args, **kwargs: FakeResponse(bad_source)).feed()
        bad_point = {"topic_id": "topic-1", "points": [{"observed_at": "2026-08-09T00:00:00Z", "opportunity_score": "high"}]}
        with self.assertRaisesRegex(TopicRadarProtocolError, "opportunity_score"):
            TopicRadarClient(base_url="https://example.test", opener=lambda *args, **kwargs: FakeResponse(bad_point)).history("topic-1")

    def test_public_client_exposes_no_server_model_method(self) -> None:
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(sample_feed()),
        )
        self.assertFalse(hasattr(client, "insight"))
        self.assertFalse(hasattr(client, "insight_timeout"))

    def test_cli_exposes_only_feed_sources_history(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(HELPER), "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("feed", help_result.stdout)
        self.assertIn("sources", help_result.stdout)
        self.assertIn("history", help_result.stdout)
        self.assertNotIn("insight", help_result.stdout.lower())
        self.assertNotIn("insight-timeout", help_result.stdout.lower())

        rejected = subprocess.run(
            [sys.executable, str(HELPER), "insight", "topic-1"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("invalid choice", rejected.stderr.lower())

    def test_all_public_operations_are_get_without_request_body(self) -> None:
        calls = []
        responses = iter(
            [
                sample_feed(),
                {"generated_at": "2026-08-09T00:00:00Z", "sources": []},
                {"topic_id": "topic-1", "points": []},
            ]
        )

        def opener(request, timeout):
            calls.append(request)
            return FakeResponse(next(responses))

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        client.feed(limit=1)
        client.sources()
        client.history("topic-1")

        self.assertEqual(len(calls), 3)
        for request in calls:
            self.assertEqual(request.get_method(), "GET")
            self.assertIsNone(request.data)
            self.assertNotIn("/insight", request.full_url)

    def test_feed_rejects_malformed_payload(self) -> None:
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse({"items": []}),
        )
        with self.assertRaises(TopicRadarProtocolError):
            client.feed()

    def test_network_error_is_normalized(self) -> None:
        def opener(request, timeout):
            raise URLError("offline")

        client = TopicRadarClient(base_url="https://example.test", opener=opener)
        with self.assertRaisesRegex(TopicRadarError, r"example\.test.*offline"):
            client.sources()

    def test_rejects_invalid_signal(self) -> None:
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(sample_feed()),
        )
        with self.assertRaises(ValueError):
            client.feed(signal="invented")

    def test_rejects_relative_or_non_http_base_url(self) -> None:
        for value in ("/local", "file:///tmp/radar.json", "javascript:alert(1)", "https://user:secret@example.test", "https://example.test/path"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TopicRadarClient(base_url=value)

    def test_environment_origin_is_explicitly_reported(self) -> None:
        previous = os.environ.get("AIWORKSTATION_TOPIC_RADAR_BASE_URL")
        stream = io.StringIO()
        try:
            os.environ["AIWORKSTATION_TOPIC_RADAR_BASE_URL"] = "http://radar.dev.test"
            with contextlib.redirect_stderr(stream):
                client = TopicRadarClient()
        finally:
            if previous is None:
                os.environ.pop("AIWORKSTATION_TOPIC_RADAR_BASE_URL", None)
            else:
                os.environ["AIWORKSTATION_TOPIC_RADAR_BASE_URL"] = previous
        self.assertFalse(client.uses_official_origin)
        self.assertEqual(client.origin_source, "environment")
        self.assertIn("non-official Topic Radar origin http://radar.dev.test", stream.getvalue())

    def test_rejects_oversized_response_and_invalid_freshness_types(self) -> None:
        oversized = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(b"{" + b" " * (4 * 1024 * 1024) + b"}"),
        )
        with self.assertRaisesRegex(TopicRadarProtocolError, "size limit"):
            oversized.feed()

        malformed = sample_feed()
        malformed["snapshot_age_seconds"] = "recent"
        client = TopicRadarClient(
            base_url="https://example.test",
            opener=lambda request, timeout: FakeResponse(malformed),
        )
        with self.assertRaisesRegex(TopicRadarProtocolError, "snapshot_age_seconds"):
            client.feed()


if __name__ == "__main__":
    unittest.main()
