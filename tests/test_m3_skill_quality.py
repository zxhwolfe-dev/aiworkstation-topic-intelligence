from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zipfile import ZipFile

from scripts.build_release import REQUIRED_SKILL_FILES, build_release


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("topic-intelligence",)


class _RadarHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path.startswith("/api/v1/ai/topic-radar/feed"):
            payload = {
                "generated_at": "2026-08-09T06:00:00Z",
                "status": "ok",
                "partial": False,
                "stale": False,
                "snapshot_age_seconds": 12,
                "refreshing": False,
                "history_available": True,
                "source_status": [],
                "items": [
                    {
                        "id": "topic:test-standalone",
                        "title": "Standalone test topic",
                        "trend_stage": "rising",
                        "opportunity_score": 80,
                        "evidence": [],
                        "trend": {},
                    }
                ],
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


class M3SkillQualityTests(unittest.TestCase):
    def test_v0_2_release_history_is_preserved_under_current_v0_3_line(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.3.0")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        acceptance = (
            ROOT / "docs" / "m3.1-final-acceptance-2026-08-09.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## [0.3.0]", changelog)
        self.assertIn("## [0.2.1] - 2026-08-10", changelog)
        self.assertIn("## [0.2.0] - 2026-08-09", changelog)
        self.assertIn("## [0.1.0] - 2026-08-09", changelog)
        self.assertIn("M3_1_SKILL_QUALITY_PASS", acceptance)
        self.assertIn("HANDOFF_STATUS: PASS", acceptance)

    def test_skill_local_helpers_match_canonical_root_helper_byte_for_byte(self) -> None:
        canonical = (ROOT / "scripts" / "topic_radar_client.py").read_bytes()
        for name in SKILLS:
            bundled = ROOT / "skills" / name / "scripts" / "topic_radar_client.py"
            self.assertTrue(bundled.is_file())
            self.assertEqual(bundled.read_bytes(), canonical, name)

    def test_unified_skill_contract_has_composition_boundary(self) -> None:
        source = (ROOT / "skills" / SKILLS[0] / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Mode 3: selection followed by brief", source)
        self.assertIn("Do not run a second feed", source)
        self.assertIn("preserve its exact feed", source)

    def test_unified_skill_defines_three_modes(self) -> None:
        source = (ROOT / "skills" / SKILLS[0] / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Mode 1: selection only", source)
        self.assertIn("Mode 2: brief for a supplied current topic", source)
        self.assertIn("Mode 3: selection followed by brief", source)

    def test_release_archives_include_required_standalone_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            manifest = build_release(Path(output_dir), root=ROOT)
            for item in manifest["artifacts"]:
                with ZipFile(Path(output_dir) / item["file"]) as archive:
                    names = set(archive.namelist())
                prefix = f'{item["skill"]}/'
                for relative in REQUIRED_SKILL_FILES:
                    self.assertIn(prefix + relative, names)
                self.assertIn(prefix + "LICENSE", names)

    def test_each_extracted_release_helper_executes_feed_without_repository_root(self) -> None:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), _RadarHandler)
        except PermissionError as exc:
            self.skipTest(
                "loopback socket bind is unavailable in this sandbox; "
                f"standalone HTTP E2E remains covered by normal CI: {exc}"
            )

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as extract_dir, tempfile.TemporaryDirectory() as outside_dir:
                manifest = build_release(Path(output_dir), root=ROOT)
                for item in manifest["artifacts"]:
                    archive_path = Path(output_dir) / item["file"]
                    destination = Path(extract_dir) / item["skill"]
                    destination.mkdir()
                    with ZipFile(archive_path) as archive:
                        archive.extractall(destination)
                    helper = destination / item["skill"] / "scripts" / "topic_radar_client.py"
                    completed = subprocess.run(
                        [sys.executable, str(helper), "--base-url", base_url, "feed", "--limit", "1"],
                        cwd=outside_dir,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    payload = json.loads(completed.stdout)
                    self.assertEqual(payload["items"][0]["id"], "topic:test-standalone")

                    help_result = subprocess.run(
                        [sys.executable, str(helper), "--help"],
                        cwd=outside_dir,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10,
                    )
                    self.assertEqual(help_result.returncode, 0, help_result.stderr)
                    self.assertNotIn("insight", help_result.stdout.lower())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_historical_m3_quality_matrix_remains_available(self) -> None:
        payload = json.loads(
            (ROOT / "evals" / "m3-skill-quality.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema"], "ati.m3-skill-quality.v1")
        cases = payload["cases"]
        self.assertGreaterEqual(len(cases), 24)
        ids = {case["id"] for case in cases}
        required = {
            "daily-scan-zh-dual",
            "cross-market-early-opportunity-en",
            "composed-pick-and-brief-zh",
            "brief-valid-current-task-handoff",
            "brief-only-pick-best-fallback",
            "invalid-topic-id",
            "no-useful-candidate",
            "stale-feed-blocks-current-claim",
            "partial-feed-surfaces-gap",
            "source-empty-is-not-outage",
            "source-error-limits-comparison",
            "refreshing-non-atomic-history",
            "feed-unavailable-blocked",
            "stale-persisted-handoff-rejected",
            "handoff-identity-mismatch-rejected",
            "creator-only-install",
        }
        self.assertTrue(required.issubset(ids))
        self.assertTrue(any(case["locale"] == "en" for case in cases))
        self.assertTrue(any(case["locale"] == "zh" for case in cases))
        dimensions = set(payload["acceptance_dimensions"])
        self.assertIn("standalone_skill_runtime", dimensions)
        self.assertIn("handoff_continuity", dimensions)
        self.assertIn("task_completion_quality", dimensions)


if __name__ == "__main__":
    unittest.main()
