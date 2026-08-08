#!/usr/bin/env python3
"""Install Topic Intelligence skills into Codex's user skill directory.

The installer uses symlinks so the checked-out repository remains the source of
truth. It never overwrites an existing unrelated skill directory or symlink.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, Optional


SKILL_NAMES = (
    "cross-market-trend-research",
    "evidence-backed-content-brief",
)


class InstallError(RuntimeError):
    """Raised when a safe install/uninstall operation cannot continue."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_target_root() -> Path:
    configured = os.getenv("AIWORKSTATION_CODEX_SKILLS_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".agents" / "skills"


def skill_sources(root: Optional[Path] = None) -> dict[str, Path]:
    repo = (root or repository_root()).resolve()
    result = {name: (repo / "skills" / name).resolve() for name in SKILL_NAMES}
    missing = [name for name, path in result.items() if not (path / "SKILL.md").is_file()]
    if missing:
        raise InstallError(f"missing skill source(s): {', '.join(missing)}")
    return result


def _same_symlink(destination: Path, source: Path) -> bool:
    if not destination.is_symlink():
        return False
    try:
        return destination.resolve(strict=True) == source.resolve(strict=True)
    except FileNotFoundError:
        return False


def inspect(target_root: Path, *, root: Optional[Path] = None) -> list[dict[str, str]]:
    sources = skill_sources(root)
    rows: list[dict[str, str]] = []
    for name, source in sources.items():
        destination = target_root / name
        if _same_symlink(destination, source):
            state = "installed"
        elif destination.is_symlink():
            state = "conflicting_symlink"
        elif destination.exists():
            state = "conflicting_path"
        else:
            state = "missing"
        rows.append(
            {
                "name": name,
                "state": state,
                "source": str(source),
                "destination": str(destination),
            }
        )
    return rows


def install(target_root: Path, *, root: Optional[Path] = None) -> list[dict[str, str]]:
    sources = skill_sources(root)
    target_root = target_root.expanduser()

    conflicts: list[str] = []
    for name, source in sources.items():
        destination = target_root / name
        if destination.exists() or destination.is_symlink():
            if not _same_symlink(destination, source):
                conflicts.append(f"{name}: {destination}")

    if conflicts:
        raise InstallError(
            "refusing to overwrite existing skill path(s): " + "; ".join(conflicts)
        )

    target_root.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        destination = target_root / name
        if not destination.is_symlink():
            destination.symlink_to(source, target_is_directory=True)

    return inspect(target_root, root=root)


def uninstall(target_root: Path, *, root: Optional[Path] = None) -> list[dict[str, str]]:
    sources = skill_sources(root)
    target_root = target_root.expanduser()

    for name, source in sources.items():
        destination = target_root / name
        if _same_symlink(destination, source):
            destination.unlink()

    return inspect(target_root, root=root)


def _print(rows: Iterable[dict[str, str]]) -> None:
    print(json.dumps(list(rows), ensure_ascii=False, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely symlink Topic Intelligence skills into Codex"
    )
    parser.add_argument("command", choices=("install", "status", "uninstall"))
    parser.add_argument(
        "--target-root",
        default=None,
        help="Override Codex skill root (default: $HOME/.agents/skills)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    target_root = (
        Path(args.target_root).expanduser() if args.target_root else default_target_root()
    )

    try:
        if args.command == "install":
            rows = install(target_root)
        elif args.command == "uninstall":
            rows = uninstall(target_root)
        else:
            rows = inspect(target_root)
    except InstallError as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 2

    _print(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
