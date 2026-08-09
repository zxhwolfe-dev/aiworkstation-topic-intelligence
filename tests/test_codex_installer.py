from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install_codex_skills import (
    InstallError,
    doctor,
    inspect,
    install,
    project_version,
    uninstall,
)


SKILLS = (
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)
LEGACY_SKILL = "cross-market-trend-research"


def make_fake_repo(root: Path, *, version: str = "0.2.0") -> None:
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    for name in SKILLS:
        skill = root / "skills" / name
        (skill / "agents").mkdir(parents=True)
        (skill / "scripts").mkdir(parents=True)
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n",
            encoding="utf-8",
        )
        (skill / "agents" / "openai.yaml").write_text(
            "interface:\n  display_name: Test\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "topic_radar_client.py").write_text(
            "#!/usr/bin/env python3\nprint('test helper')\n",
            encoding="utf-8",
        )
        (skill / "references" / "handoff-contract.md").write_text(
            "Schema: `ati.topic-opportunity-handoff.v1`\n",
            encoding="utf-8",
        )


class CodexInstallerTests(unittest.TestCase):
    def test_install_is_idempotent_and_uses_matching_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)

            first = install(target, root=repo)
            second = install(target, root=repo)

            self.assertEqual([row["state"] for row in first], ["installed", "installed"])
            self.assertEqual([row["state"] for row in second], ["installed", "installed"])
            for name in SKILLS:
                self.assertTrue((target / name).is_symlink())
                self.assertEqual((target / name).resolve(), (repo / "skills" / name).resolve())

    def test_install_migrates_matching_broken_legacy_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)
            target.mkdir(parents=True)

            legacy_source = repo / "skills" / LEGACY_SKILL
            legacy_link = target / LEGACY_SKILL
            legacy_link.symlink_to(legacy_source, target_is_directory=True)
            self.assertTrue(legacy_link.is_symlink())
            self.assertFalse(legacy_source.exists())

            rows = install(target, root=repo)
            report = doctor(target, root=repo)

            self.assertFalse(legacy_link.is_symlink())
            self.assertEqual([row["state"] for row in rows], ["installed", "installed"])
            self.assertTrue(report["legacy_clean"])
            self.assertTrue(report["ok"])

    def test_install_refuses_conflict_before_creating_other_links(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)
            target.mkdir(parents=True)
            (target / SKILLS[0]).mkdir()

            with self.assertRaisesRegex(InstallError, "refusing to overwrite"):
                install(target, root=repo)

            self.assertFalse((target / SKILLS[1]).exists())

    def test_uninstall_removes_only_matching_links(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)
            install(target, root=repo)

            own_link = target / SKILLS[0]
            own_link.unlink()
            unrelated = Path(target_dir) / "unrelated"
            unrelated.mkdir()
            own_link.symlink_to(unrelated, target_is_directory=True)

            rows = uninstall(target, root=repo)
            states = {row["name"]: row["state"] for row in rows}

            self.assertTrue(own_link.is_symlink())
            self.assertEqual(states[SKILLS[0]], "conflicting_symlink")
            self.assertEqual(states[SKILLS[1]], "missing")

    def test_inspect_reports_missing_without_creating_target(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "does-not-exist" / "skills"
            make_fake_repo(repo)

            rows = inspect(target, root=repo)

            self.assertEqual([row["state"] for row in rows], ["missing", "missing"])
            self.assertFalse(target.exists())

    def test_doctor_reports_version_python_metadata_and_install_health(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo, version="0.2.0")
            install(target, root=repo)

            report = doctor(target, root=repo)

            self.assertEqual(report["version"], "0.2.0")
            self.assertTrue(report["python_supported"])
            self.assertTrue(report["legacy_clean"])
            self.assertTrue(report["ok"])
            self.assertEqual(len(report["skills"]), 2)
            self.assertTrue(all(item["skill_md"] == "ok" for item in report["skills"]))
            self.assertTrue(all(item["openai_metadata"] == "ok" for item in report["skills"]))
            self.assertTrue(all(item["runtime_helper"] == "ok" for item in report["skills"]))
            self.assertTrue(all(item["handoff_contract"] == "ok" for item in report["skills"]))

    def test_doctor_fails_when_required_runtime_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)
            install(target, root=repo)
            helper = repo / "skills" / SKILLS[0] / "scripts" / "topic_radar_client.py"
            helper.unlink()

            report = doctor(target, root=repo)

            self.assertFalse(report["ok"])
            first = next(item for item in report["skills"] if item["name"] == SKILLS[0])
            self.assertEqual(first["state"], "installed")
            self.assertEqual(first["runtime_helper"], "missing")

    def test_doctor_fails_when_handoff_contract_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as target_dir:
            repo = Path(repo_dir)
            target = Path(target_dir) / "skills"
            make_fake_repo(repo)
            install(target, root=repo)
            contract = repo / "skills" / SKILLS[1] / "references" / "handoff-contract.md"
            contract.unlink()

            report = doctor(target, root=repo)

            self.assertFalse(report["ok"])
            second = next(item for item in report["skills"] if item["name"] == SKILLS[1])
            self.assertEqual(second["handoff_contract"], "missing")

    def test_project_version_rejects_invalid_value(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir:
            repo = Path(repo_dir)
            make_fake_repo(repo, version="banana")
            with self.assertRaisesRegex(InstallError, "invalid VERSION"):
                project_version(repo)


if __name__ == "__main__":
    unittest.main()
