from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install_codex_skills import InstallError, inspect, install, uninstall


SKILLS = (
    "cross-market-trend-research",
    "evidence-backed-content-brief",
)


def make_fake_repo(root: Path) -> None:
    for name in SKILLS:
        skill = root / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n",
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


if __name__ == "__main__":
    unittest.main()
