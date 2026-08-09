from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.build_release import (
    LICENSE_ID,
    MANIFEST_SCHEMA,
    REQUIRED_SKILL_FILES,
    ReleaseError,
    build_release,
    read_version,
)


SKILLS = (
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)
HELPER_TEXT = "#!/usr/bin/env python3\nprint('Thin client test helper')\n"
HANDOFF_TEXT = "Schema: `ati.topic-opportunity-handoff.v1`\n"


def make_release_repo(root: Path, *, version: str = "0.1.0") -> None:
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    (root / "LICENSE").write_text("Apache License 2.0 test fixture\n", encoding="utf-8")
    (root / "scripts").mkdir(parents=True)
    (root / "references").mkdir(parents=True)
    (root / "scripts" / "topic_radar_client.py").write_text(HELPER_TEXT, encoding="utf-8")
    (root / "references" / "topic-opportunity-handoff.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    for name in SKILLS:
        skill = root / "skills" / name
        (skill / "agents").mkdir(parents=True)
        (skill / "scripts").mkdir(parents=True)
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: release test\n---\n",
            encoding="utf-8",
        )
        (skill / "agents" / "openai.yaml").write_text(
            "interface:\n  display_name: Test\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "topic_radar_client.py").write_text(HELPER_TEXT, encoding="utf-8")
        (skill / "references" / "handoff-contract.md").write_text(HANDOFF_TEXT, encoding="utf-8")


class ReleaseBuilderTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_version_must_be_semver(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir:
            repo = Path(repo_dir)
            make_release_repo(repo, version="not-a-version")
            with self.assertRaisesRegex(ReleaseError, "semantic VERSION"):
                read_version(repo)

    def test_build_creates_manifest_checksums_and_one_archive_per_skill(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            output = Path(out_dir)
            make_release_repo(repo)

            manifest = build_release(output, root=repo)

            self.assertEqual(manifest["schema"], MANIFEST_SCHEMA)
            self.assertEqual(manifest["version"], "0.1.0")
            self.assertEqual(manifest["license"], LICENSE_ID)
            self.assertEqual({item["skill"] for item in manifest["artifacts"]}, set(SKILLS))
            disk_manifest = json.loads((output / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(disk_manifest, manifest)
            sums = (output / "SHA256SUMS").read_text(encoding="utf-8")
            for item in manifest["artifacts"]:
                archive = output / item["file"]
                self.assertTrue(archive.is_file())
                self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), item["sha256"])
                self.assertIn(item["sha256"], sums)
                self.assertIn(item["file"], sums)

    def test_archives_are_deterministic_self_contained_and_licensed(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            noise = repo / "skills" / SKILLS[0] / "__pycache__"
            noise.mkdir()
            (noise / "ignored.pyc").write_bytes(b"noise")

            first = build_release(Path(first_dir), root=repo)
            second = build_release(Path(second_dir), root=repo)
            self.assertEqual(
                {item["skill"]: item["sha256"] for item in first["artifacts"]},
                {item["skill"]: item["sha256"] for item in second["artifacts"]},
            )

            for item in first["artifacts"]:
                with ZipFile(Path(first_dir) / item["file"]) as archive:
                    names = archive.namelist()
                prefix = item["skill"] + "/"
                for relative in REQUIRED_SKILL_FILES:
                    self.assertIn(prefix + relative, names)
                self.assertIn(prefix + "LICENSE", names)
                self.assertTrue(all(name.startswith(prefix) for name in names))
                self.assertFalse(any("__pycache__" in name for name in names))

    def test_release_rejects_missing_standalone_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            (repo / "skills" / SKILLS[0] / "scripts" / "topic_radar_client.py").unlink()
            with self.assertRaisesRegex(ReleaseError, "scripts/topic_radar_client.py"):
                build_release(Path(out_dir), root=repo)

    def test_release_rejects_missing_handoff_contract(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            (repo / "skills" / SKILLS[1] / "references" / "handoff-contract.md").unlink()
            with self.assertRaisesRegex(ReleaseError, "references/handoff-contract.md"):
                build_release(Path(out_dir), root=repo)

    def test_release_rejects_drifted_helper(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            (repo / "skills" / SKILLS[0] / "scripts" / "topic_radar_client.py").write_text("drifted\n", encoding="utf-8")
            with self.assertRaisesRegex(ReleaseError, "portable runtime drift"):
                build_release(Path(out_dir), root=repo)

    def test_release_rejects_drifted_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            (repo / "skills" / SKILLS[1] / "references" / "handoff-contract.md").write_text("drifted\n", encoding="utf-8")
            with self.assertRaisesRegex(ReleaseError, "portable runtime drift"):
                build_release(Path(out_dir), root=repo)

    def test_release_rejects_symlinks_inside_skill_package(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            target = repo / "outside.txt"
            target.write_text("outside", encoding="utf-8")
            link = repo / "skills" / SKILLS[0] / "linked.txt"
            link.symlink_to(target)
            with self.assertRaisesRegex(ReleaseError, "symlink not allowed"):
                build_release(Path(out_dir), root=repo)

    def test_release_requires_repository_license(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as out_dir:
            repo = Path(repo_dir)
            make_release_repo(repo)
            (repo / "LICENSE").unlink()
            with self.assertRaisesRegex(ReleaseError, "LICENSE file is missing"):
                build_release(Path(out_dir), root=repo)

    def test_current_repository_builds_real_skill_archives(self) -> None:
        with tempfile.TemporaryDirectory() as out_dir:
            output = Path(out_dir)
            manifest = build_release(output, root=self.ROOT)
            self.assertEqual(manifest["version"], read_version(self.ROOT))
            self.assertEqual(manifest["license"], "Apache-2.0")
            self.assertEqual(len(manifest["artifacts"]), 2)
            for item in manifest["artifacts"]:
                with ZipFile(output / item["file"]) as archive:
                    names = archive.namelist()
                prefix = f'{item["skill"]}/'
                for relative in REQUIRED_SKILL_FILES:
                    self.assertIn(prefix + relative, names)
                self.assertIn(prefix + "LICENSE", names)

    def test_repository_release_metadata_is_consistent(self) -> None:
        version = read_version(self.ROOT)
        changelog = (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        distribution = (self.ROOT / "docs" / "distribution.md").read_text(encoding="utf-8")
        checklist = (self.ROOT / "docs" / "release-checklist.md").read_text(encoding="utf-8")
        license_text = (self.ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog)
        self.assertIn("scripts/build_release.py", distribution)
        self.assertIn("release-manifest.json", distribution)
        self.assertIn("scripts/topic_radar_client.py", distribution)
        self.assertIn("references/handoff-contract.md", distribution)
        self.assertIn("Apache", license_text)
        self.assertIn("v${VERSION}", checklist)

    def test_tag_release_workflow_validates_version_before_publishing(self) -> None:
        workflow = (self.ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn('tags: ["v*"]', workflow)
        self.assertIn('GITHUB_REF_NAME#v', workflow)
        self.assertIn('python3 scripts/build_release.py --output dist', workflow)
        self.assertIn('gh release create', workflow)


if __name__ == "__main__":
    unittest.main()
