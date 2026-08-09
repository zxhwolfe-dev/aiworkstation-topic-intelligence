from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.sync_skill_runtime import SKILLS, SyncError, sync


ROOT = Path(__file__).resolve().parents[1]


class SkillRuntimeSyncTests(unittest.TestCase):
    def test_repository_runtime_copies_are_in_sync(self) -> None:
        self.assertEqual(sync(root=ROOT, check=True), [])

    def test_handoff_contract_matches_canonical_reference(self) -> None:
        canonical = (ROOT / "references" / "topic-opportunity-handoff.md").read_bytes()
        for skill in SKILLS:
            bundled = ROOT / "skills" / skill / "references" / "handoff-contract.md"
            self.assertEqual(bundled.read_bytes(), canonical, skill)

    def test_quality_contract_matches_canonical_reference(self) -> None:
        canonical = (
            ROOT / "references" / "topic-intelligence-quality-contract.md"
        ).read_bytes()
        for skill in SKILLS:
            bundled = ROOT / "skills" / skill / "references" / "quality-contract.md"
            self.assertEqual(bundled.read_bytes(), canonical, skill)

    @staticmethod
    def _make_fixture(root: Path, *, helper_text: str, handoff_text: str, quality_text: str) -> None:
        (root / "scripts").mkdir(parents=True)
        (root / "references").mkdir(parents=True)
        (root / "scripts" / "topic_radar_client.py").write_text(
            "canonical helper\n", encoding="utf-8"
        )
        (root / "references" / "topic-opportunity-handoff.md").write_text(
            "canonical handoff\n", encoding="utf-8"
        )
        (root / "references" / "topic-intelligence-quality-contract.md").write_text(
            "canonical quality\n", encoding="utf-8"
        )
        for skill in SKILLS:
            skill_root = root / "skills" / skill
            (skill_root / "scripts").mkdir(parents=True)
            (skill_root / "references").mkdir(parents=True)
            (skill_root / "scripts" / "topic_radar_client.py").write_text(
                helper_text, encoding="utf-8"
            )
            (skill_root / "references" / "handoff-contract.md").write_text(
                handoff_text, encoding="utf-8"
            )
            (skill_root / "references" / "quality-contract.md").write_text(
                quality_text, encoding="utf-8"
            )

    def test_check_reports_drift_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._make_fixture(
                root,
                helper_text="drifted\n",
                handoff_text="canonical handoff\n",
                quality_text="canonical quality\n",
            )

            before = (
                root / "skills" / SKILLS[0] / "scripts" / "topic_radar_client.py"
            ).read_text(encoding="utf-8")
            with self.assertRaisesRegex(SyncError, "out of sync"):
                sync(root=root, check=True)
            after = (
                root / "skills" / SKILLS[0] / "scripts" / "topic_radar_client.py"
            ).read_text(encoding="utf-8")
            self.assertEqual(before, after)

    def test_sync_repairs_runtime_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._make_fixture(
                root,
                helper_text="old helper\n",
                handoff_text="old handoff\n",
                quality_text="old quality\n",
            )

            changed = sync(root=root)
            self.assertEqual(len(changed), 6)
            self.assertEqual(sync(root=root, check=True), [])


if __name__ == "__main__":
    unittest.main()
