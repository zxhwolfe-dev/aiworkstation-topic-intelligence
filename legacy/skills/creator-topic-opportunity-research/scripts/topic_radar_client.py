#!/usr/bin/env python3
"""Thin no-cost client for the public AI Workstation Global Topic Radar API.

The distributable Skills intentionally expose only non-LLM Radar reads. Premium
server-side Topic Insight is not part of this bundled helper because anonymous
Skill usage must not consume AI Workstation model quota.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import urlsplit
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://aiworkstation.cn"
API_PATH = "/api/v1/ai/topic-radar"
DEFAULT_TIMEOUT = 15.0
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_ALLOWED_SIGNALS = {"", "all", "multi_source", "early_opportunity", "single_source"}


class TopicRadarError(RuntimeError):
    """Base error for request, HTTP, and public-contract failures."""


class TopicRadarProtocolError(TopicRadarError):
    """Raised when the public endpoint returns an unexpected JSON shape."""


def _json_object(value: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TopicRadarProtocolError(f"{context}: expected JSON object")
    return value


def _require_list(payload: Mapping[str, Any], key: str, *, context: str) -> None:
    if key not in payload or not isinstance(payload[key], list):
        raise TopicRadarProtocolError(f"{context}: expected list field {key!r}")


def _validate_feed_items(items: list[Any]) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TopicRadarProtocolError(f"feed: item {index} is not an object")
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            raise TopicRadarProtocolError(
                f"feed: item {index} missing stable string field 'id'"
            )


def _validate_payload(kind: str, payload: Any) -> dict[str, Any]:
    obj = _json_object(payload, context=kind)

    if kind == "feed":
        for key in ("generated_at", "status", "partial", "stale"):
            if key not in obj:
                raise TopicRadarProtocolError(f"feed: missing field {key!r}")
        if not isinstance(obj["generated_at"], str) or not obj["generated_at"].strip():
            raise TopicRadarProtocolError("feed: generated_at must be a non-empty string")
        if not isinstance(obj["status"], str) or not obj["status"].strip():
            raise TopicRadarProtocolError("feed: status must be a non-empty string")
        _require_list(obj, "items", context="feed")
        _require_list(obj, "source_status", context="feed")
        _validate_feed_items(obj["items"])
        for index, item in enumerate(obj["source_status"]):
            if not isinstance(item, dict):
                raise TopicRadarProtocolError(f"feed: source_status item {index} is not an object")
            for field in ("id", "status"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise TopicRadarProtocolError(f"feed: source_status item {index} missing string field {field!r}")
        if not isinstance(obj.get("partial"), bool) or not isinstance(obj.get("stale"), bool):
            raise TopicRadarProtocolError("feed: partial and stale must be boolean")
        for key in ("refreshing", "history_available"):
            if key in obj and not isinstance(obj[key], bool):
                raise TopicRadarProtocolError(f"feed: {key} must be boolean")
        if "snapshot_age_seconds" in obj and (isinstance(obj["snapshot_age_seconds"], bool) or not isinstance(obj["snapshot_age_seconds"], int) or obj["snapshot_age_seconds"] < 0):
            raise TopicRadarProtocolError("feed: snapshot_age_seconds must be a non-negative integer")
    elif kind == "sources":
        if "generated_at" not in obj:
            raise TopicRadarProtocolError("sources: missing field 'generated_at'")
        if not isinstance(obj["generated_at"], str) or not obj["generated_at"].strip():
            raise TopicRadarProtocolError("sources: generated_at must be a non-empty string")
        _require_list(obj, "sources", context="sources")
        if "snapshot_age_seconds" in obj and (isinstance(obj["snapshot_age_seconds"], bool) or not isinstance(obj["snapshot_age_seconds"], int) or obj["snapshot_age_seconds"] < 0):
            raise TopicRadarProtocolError("sources: snapshot_age_seconds must be a non-negative integer")
        if "refreshing" in obj and not isinstance(obj["refreshing"], bool):
            raise TopicRadarProtocolError("sources: refreshing must be boolean")
    elif kind == "history":
        if not isinstance(obj.get("topic_id"), str):
            raise TopicRadarProtocolError("history: expected string field 'topic_id'")
        _require_list(obj, "points", context="history")
        for index, item in enumerate(obj["points"]):
            if not isinstance(item, dict):
                raise TopicRadarProtocolError(f"history: point {index} is not an object")
            if not isinstance(item.get("observed_at"), str) or not item["observed_at"].strip():
                raise TopicRadarProtocolError(f"history: point {index} missing string field 'observed_at'")
            score = item.get("opportunity_score")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise TopicRadarProtocolError(f"history: point {index} opportunity_score must be numeric")

    return obj


class TopicRadarClient:
    """Read-only public Radar client with no local persistence or model calls."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        configured_env = os.getenv("AIWORKSTATION_TOPIC_RADAR_BASE_URL", "").strip()
        selected = (base_url or configured_env or DEFAULT_BASE_URL).rstrip("/")
        parsed = urlsplit(selected)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute http(s) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("base_url must be a credential-free origin")
        if parsed.path not in {"", "/"}:
            raise ValueError("base_url must not include a path")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = selected
        self.uses_official_origin = selected == DEFAULT_BASE_URL
        self.origin_source = "explicit" if base_url else ("environment" if configured_env else "default")
        if configured_env and not base_url and selected != DEFAULT_BASE_URL:
            print(
                f"warning: using non-official Topic Radar origin {selected} from AIWORKSTATION_TOPIC_RADAR_BASE_URL; "
                "use only for explicitly requested development/self-hosted testing",
                file=sys.stderr,
            )
        self.timeout = float(timeout)
        self._opener = opener or urlopen

    def _request(
        self,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        kind: str,
    ) -> dict[str, Any]:
        query: dict[str, str] = {}
        for key, value in (params or {}).items():
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                query[key] = "true" if value else "false"
            else:
                query[key] = str(value)

        url = f"{self.base_url}{API_PATH}{endpoint}"
        if query:
            url = f"{url}?{urlencode(query)}"

        request = Request(
            url=url,
            headers={
                "Accept": "application/json",
                "User-Agent": "aiworkstation-topic-intelligence-public-skill",
            },
            method="GET",
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                try:
                    raw = response.read(MAX_RESPONSE_BYTES + 1)
                except TypeError:  # tiny test doubles may expose read() only
                    raw = response.read()
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise TopicRadarProtocolError("Topic Radar response exceeded size limit")
        except HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            suffix = f": {detail}" if detail else ""
            raise TopicRadarError(f"HTTP {exc.code} from Topic Radar ({self.base_url}){suffix}") from exc
        except URLError as exc:
            raise TopicRadarError(f"Topic Radar request failed ({self.base_url}): {exc.reason}") from exc
        except TimeoutError as exc:
            raise TopicRadarError(f"Topic Radar request timed out ({self.base_url})") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TopicRadarProtocolError("Topic Radar returned invalid JSON") from exc

        return _validate_payload(kind, payload)

    def feed(
        self,
        *,
        q: str = "",
        platform: str = "",
        target_platform: str = "",
        region: str = "",
        category: str = "",
        source: str = "",
        stage: str = "",
        signal: str = "",
        keywords: str = "",
        exclude_sources: str = "",
        min_score: int = 0,
        new_only: bool = False,
        max_age_hours: Optional[int] = None,
        offset: int = 0,
        limit: int = 24,
    ) -> dict[str, Any]:
        if signal not in _ALLOWED_SIGNALS:
            raise ValueError(f"unsupported signal: {signal}")
        if not 0 <= min_score <= 100:
            raise ValueError("min_score must be between 0 and 100")
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        if max_age_hours is not None and not 1 <= max_age_hours <= 8760:
            raise ValueError("max_age_hours must be between 1 and 8760")

        return self._request(
            "/feed",
            params={
                "q": q,
                "platform": platform,
                "target_platform": target_platform,
                "region": region,
                "category": category,
                "source": source,
                "stage": stage,
                "signal": signal,
                "keywords": keywords,
                "exclude_sources": exclude_sources,
                "min_score": min_score if min_score else None,
                "new_only": new_only if new_only else None,
                "max_age_hours": max_age_hours,
                "offset": offset if offset else None,
                "limit": limit,
            },
            kind="feed",
        )

    def sources(self) -> dict[str, Any]:
        return self._request("/sources", kind="sources")

    def history(self, topic_id: str) -> dict[str, Any]:
        topic_id = topic_id.strip()
        if not topic_id:
            raise ValueError("topic_id is required")
        payload = self._request(
            "/history",
            params={"topic_id": topic_id},
            kind="history",
        )
        if payload["topic_id"] != topic_id:
            raise TopicRadarProtocolError(
                "history: response topic_id does not match requested topic_id"
            )
        return payload


def _dump(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read public no-cost AI Workstation Global Topic Radar data"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Explicit custom Radar origin for development/self-hosted testing; "
            f"normal public Skill workflows use {DEFAULT_BASE_URL}"
        ),
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    sub = parser.add_subparsers(dest="command", required=True)

    feed = sub.add_parser("feed", help="Read the current topic feed")
    feed.add_argument("--q", default="")
    feed.add_argument("--platform", default="")
    feed.add_argument("--region", default="")
    feed.add_argument("--category", default="")
    feed.add_argument("--source", default="")
    feed.add_argument("--stage", default="")
    feed.add_argument("--signal", choices=sorted(_ALLOWED_SIGNALS), default="")
    feed.add_argument("--keywords", default="")
    feed.add_argument("--exclude-sources", default="")
    feed.add_argument("--min-score", type=int, default=0)
    feed.add_argument("--new-only", action="store_true")
    feed.add_argument("--max-age-hours", type=int)
    feed.add_argument("--offset", type=int, default=0)
    feed.add_argument("--limit", type=int, default=24)

    sub.add_parser("sources", help="Read source health")

    feed.add_argument("--target-platform", default="")
    history = sub.add_parser("history", help="Read one topic's trend history")
    history.add_argument("topic_id")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        client = TopicRadarClient(base_url=args.base_url, timeout=args.timeout)
        if args.command == "feed":
            payload = client.feed(
                q=args.q,
                platform=args.platform,
                target_platform=args.target_platform,
                region=args.region,
                category=args.category,
                source=args.source,
                stage=args.stage,
                signal=args.signal,
                keywords=args.keywords,
                exclude_sources=args.exclude_sources,
                min_score=args.min_score,
                new_only=args.new_only,
                max_age_hours=args.max_age_hours,
                offset=args.offset,
                limit=args.limit,
            )
        elif args.command == "sources":
            payload = client.sources()
        else:
            payload = client.history(args.topic_id)
    except (TopicRadarError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _dump(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
