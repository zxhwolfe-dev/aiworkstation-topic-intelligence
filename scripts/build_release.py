#!/usr/bin/env python3
"""Build deterministic distributable archives for Topic Intelligence Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo


SKILL_NAMES = (
    "topic-intelligence",
)
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/topic_radar_client.py",
    "references/quality-contract.md",
    "references/selection-workflow.md",
    "references/brief-workflow.md",
)
CANONICAL_PORTABLE_FILES = {
    "scripts/topic_radar_client.py": "scripts/topic_radar_client.py",
    "references/quality-contract.md": "references/topic-intelligence-quality-contract.md",
    "references/selection-workflow.md": "references/topic-intelligence-selection-workflow.md",
    "references/brief-workflow.md": "references/topic-intelligence-brief-workflow.md",
}
VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"
)
MANIFEST_SCHEMA = "ati.release.v1"
LICENSE_ID = "Apache-2.0"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_NAMES = {".DS_Store"}


class ReleaseError(RuntimeError):
    """Raised when a release archive cannot be built safely."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_version(root: Path | None = None) -> str:
    repo = (root or repository_root()).resolve()
    version_file = repo / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ReleaseError("VERSION file is missing") from exc
    if not VERSION_RE.fullmatch(version):
        raise ReleaseError(f"invalid semantic VERSION: {version!r}")
    return version


def _license_file(repo: Path) -> Path:
    license_path = repo / "LICENSE"
    if license_path.is_symlink():
        raise ReleaseError("repository LICENSE must not be a symlink")
    if not license_path.is_file():
        raise ReleaseError("repository LICENSE file is missing")
    return license_path


def _validate_portable_runtime(repo: Path, skill_dir: Path) -> None:
    for bundled_relative, canonical_relative in CANONICAL_PORTABLE_FILES.items():
        canonical = repo / canonical_relative
        bundled = skill_dir / bundled_relative
        if not canonical.is_file():
            raise ReleaseError(f"missing canonical portable source: {canonical_relative}")
        if not bundled.is_file():
            raise ReleaseError(f"{skill_dir.name}: missing required file: {bundled_relative}")
        if canonical.read_bytes() != bundled.read_bytes():
            raise ReleaseError(
                f"{skill_dir.name}: portable runtime drift for {bundled_relative}; "
                f"run scripts/sync_skill_runtime.py"
            )


def _skill_files(skill_dir: Path) -> list[Path]:
    required = tuple(skill_dir / relative for relative in REQUIRED_SKILL_FILES)
    missing = [str(path.relative_to(skill_dir)) for path in required if not path.is_file()]
    if missing:
        raise ReleaseError(
            f"{skill_dir.name}: missing required file(s): {', '.join(missing)}"
        )

    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ReleaseError(f"{skill_dir.name}: symlink not allowed in release: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.name in IGNORED_NAMES or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return files


def _zip_info(archive_path: str) -> ZipInfo:
    info = ZipInfo(archive_path, date_time=ZIP_TIMESTAMP)
    info.compress_type = ZIP_STORED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def _write_skill_archive(skill_dir: Path, destination: Path, *, license_path: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_STORED) as archive:
        for source in _skill_files(skill_dir):
            relative = source.relative_to(skill_dir).as_posix()
            archive_path = f"{skill_dir.name}/{relative}"
            archive.writestr(_zip_info(archive_path), source.read_bytes())
        archive.writestr(
            _zip_info(f"{skill_dir.name}/LICENSE"),
            license_path.read_bytes(),
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(output_dir: Path, *, root: Path | None = None) -> dict[str, object]:
    repo = (root or repository_root()).resolve()
    version = read_version(repo)
    license_path = _license_file(repo)
    output = output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, object]] = []
    expected_names: set[str] = set()

    for skill_name in SKILL_NAMES:
        skill_dir = repo / "skills" / skill_name
        if not skill_dir.is_dir():
            raise ReleaseError(f"missing skill directory: {skill_name}")
        _validate_portable_runtime(repo, skill_dir)
        # The v0.3 product line has one public Skill and one archive. Keep the
        # asset name short while retaining the product identity and version.
        filename = f"{skill_name}-{version}.zip"
        expected_names.add(filename)
        destination = output / filename
        _write_skill_archive(skill_dir, destination, license_path=license_path)
        artifacts.append(
            {
                "skill": skill_name,
                "file": filename,
                "sha256": sha256_file(destination),
                "bytes": destination.stat().st_size,
            }
        )

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "name": "aiworkstation-topic-intelligence",
        "version": version,
        "license": LICENSE_ID,
        "artifacts": artifacts,
    }

    manifest_path = output / "release-manifest.json"
    sums_path = output / "SHA256SUMS"
    expected_names.update({manifest_path.name, sums_path.name})

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sums_path.write_text(
        "".join(f'{item["sha256"]}  {item["file"]}\n' for item in artifacts),
        encoding="utf-8",
    )

    # Clean only stale ZIPs produced by this builder; preserve unrelated files.
    prefix = f"{SKILL_NAMES[0]}-"
    for path in output.iterdir():
        if (
            path.is_file()
            and path.name.startswith(prefix)
            and path.suffix == ".zip"
            and path.name not in expected_names
        ):
            path.unlink()

    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build deterministic Topic Intelligence Skill archives"
    )
    parser.add_argument("--output", default="dist")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        manifest = build_release(Path(args.output))
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
