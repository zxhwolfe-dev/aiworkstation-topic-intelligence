from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.sync_skill_runtime import SKILLS, SyncError, sync


ROOT = Path(__file__).resolve().parents[1]


class SkillRuntimeSyncTests(unittest.TestCase):
    def test_repository_runtime_copies_are_in_sync(self) -> None:
        self.assertEqual(sync(root=ROOT, check=True), [])

    def test_selection_and_brief_workflows_match_canonical_references(self) -> None:
        for canonical_name, bundled_name in (
            ("topic-intelligence-selection-workflow.md", "selection-workflow.md"),
            ("topic-intelligence-brief-workflow.md", "brief-workflow.md"),
        ):
            canonical = (ROOT / "references" / canonical_name).read_bytes()
            for skill in SKILLS:
                bundled = ROOT / "skills" / skill / "references" / bundled_name
                self.assertEqual(bundled.read_bytes(), canonical, skill)

    def test_quality_contract_matches_canonical_reference(self) -> None:
        canonical = (
            ROOT / "references" / "topic-intelligence-quality-contract.md"
        ).read_bytes()
        for skill in SKILLS:
            bundled = ROOT / "skills" / skill / "references" / "quality-contract.md"
            self.assertEqual(bundled.read_bytes(), canonical, skill)

    @staticmethod
    def _make_fixture(root: Path, *, helper_text: str, selection_text: str, brief_text: str, quality_text: str) -> None:
        (root / "scripts").mkdir(parents=True)
        (root / "references").mkdir(parents=True)
        (root / "scripts" / "topic_radar_client.py").write_text(
            "canonical helper\n", encoding="utf-8"
        )
        (root / "references" / "topic-intelligence-quality-contract.md").write_text(
            "canonical quality\n", encoding="utf-8"
        )
        (root / "references" / "topic-intelligence-selection-workflow.md").write_text(
            "canonical selection\n", encoding="utf-8"
        )
        (root / "references" / "topic-intelligence-brief-workflow.md").write_text(
            "canonical brief\n", encoding="utf-8"
        )
        for skill in SKILLS:
            skill_root = root / "skills" / skill
            (skill_root / "scripts").mkdir(parents=True)
            (skill_root / "references").mkdir(parents=True)
            (skill_root / "scripts" / "topic_radar_client.py").write_text(
                helper_text, encoding="utf-8"
            )
            (skill_root / "references" / "quality-contract.md").write_text(
                quality_text, encoding="utf-8"
            )
            (skill_root / "references" / "selection-workflow.md").write_text(
                selection_text, encoding="utf-8"
            )
            (skill_root / "references" / "brief-workflow.md").write_text(
                brief_text, encoding="utf-8"
            )

    def test_check_reports_drift_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._make_fixture(
                root,
                helper_text="drifted\n",
                selection_text="canonical selection\n",
                brief_text="canonical brief\n",
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
                selection_text="old selection\n",
                brief_text="old brief\n",
                quality_text="old quality\n",
            )

            changed = sync(root=root)
            self.assertEqual(len(changed), 4)
            self.assertEqual(sync(root=root, check=True), [])


if __name__ == "__main__":
    unittest.main()
