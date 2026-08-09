#!/usr/bin/env python3
"""Synchronize portable Skill runtime/reference copies with canonical sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SKILLS = (
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)


class SyncError(RuntimeError):
    """Raised when portable Skill runtime copies drift from canonical sources."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def mappings(root: Path | None = None) -> list[tuple[Path, Path]]:
    repo = (root or repository_root()).resolve()
    canonical_helper = repo / "scripts" / "topic_radar_client.py"
    canonical_handoff = repo / "references" / "topic-opportunity-handoff.md"
    rows: list[tuple[Path, Path]] = []
    for skill in SKILLS:
        skill_root = repo / "skills" / skill
        rows.extend(
            [
                (canonical_helper, skill_root / "scripts" / "topic_radar_client.py"),
                (canonical_handoff, skill_root / "references" / "handoff-contract.md"),
            ]
        )
    return rows


def sync(*, root: Path | None = None, check: bool = False) -> list[str]:
    changed: list[str] = []
    repo = (root or repository_root()).resolve()
    for source, destination in mappings(repo):
        if not source.is_file():
            raise SyncError(f"missing canonical source: {source.relative_to(repo)}")
        expected = source.read_bytes()
        actual = destination.read_bytes() if destination.is_file() else None
        if actual == expected:
            continue
        relative = str(destination.relative_to(repo))
        changed.append(relative)
        if check:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(expected)
    if check and changed:
        raise SyncError("Skill runtime copies are out of sync: " + ", ".join(changed))
    return changed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync portable Topic Intelligence Skill runtime files")
    parser.add_argument("--check", action="store_true", help="fail if generated copies differ")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        changed = sync(check=bool(args.check))
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if changed:
        print("updated: " + ", ".join(changed))
    else:
        print("Skill runtime copies are in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
