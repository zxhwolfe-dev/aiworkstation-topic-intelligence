#!/usr/bin/env python3
"""Install and diagnose Topic Intelligence Skills for Codex.

The installer uses symlinks so the checked-out repository remains the source of
truth. It never overwrites an existing unrelated Skill directory or symlink.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


SKILL_NAMES = (
    "topic-intelligence",
)
LEGACY_SKILL_NAMES = (
    "cross-market-trend-research",
    "creator-topic-opportunity-research",
    "evidence-backed-content-brief",
)
VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"
)


class InstallError(RuntimeError):
    """Raised when a safe install/uninstall operation cannot continue."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_version(root: Optional[Path] = None) -> str:
    repo = (root or repository_root()).resolve()
    try:
        version = (repo / "VERSION").read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise InstallError("VERSION file is missing") from exc
    if not VERSION_RE.fullmatch(version):
        raise InstallError(f"invalid VERSION: {version!r}")
    return version


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


def _symlink_points_to(destination: Path, source: Path) -> bool:
    if not destination.is_symlink():
        return False
    try:
        raw_target = Path(os.readlink(destination))
    except OSError:
        return False
    target = raw_target if raw_target.is_absolute() else destination.parent / raw_target
    return target.resolve(strict=False) == source.resolve(strict=False)


def _same_symlink(destination: Path, source: Path) -> bool:
    return _symlink_points_to(destination, source) and source.exists()


def _legacy_rows(target_root: Path, *, root: Optional[Path] = None) -> list[dict[str, str]]:
    repo = (root or repository_root()).resolve()
    rows: list[dict[str, str]] = []
    for name in LEGACY_SKILL_NAMES:
        destination = target_root / name
        source = repo / "skills" / name
        if not destination.exists() and not destination.is_symlink():
            state = "missing"
        elif _symlink_points_to(destination, source):
            state = "legacy_project_symlink"
        elif destination.is_symlink():
            state = "conflicting_symlink"
        else:
            state = "conflicting_path"
        rows.append(
            {
                "name": name,
                "state": state,
                "source": str(source),
                "destination": str(destination),
            }
        )
    return rows


def _remove_matching_legacy_links(target_root: Path, *, root: Optional[Path] = None) -> None:
    repo = (root or repository_root()).resolve()
    for name in LEGACY_SKILL_NAMES:
        destination = target_root / name
        legacy_source = repo / "skills" / name
        if _symlink_points_to(destination, legacy_source):
            destination.unlink()


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
    repo = (root or repository_root()).resolve()
    sources = skill_sources(repo)
    target_root = target_root.expanduser()

    legacy_conflicts = [
        row for row in _legacy_rows(target_root, root=repo)
        if row["state"] not in {"missing", "legacy_project_symlink"}
    ]
    if legacy_conflicts:
        detail = "; ".join(f'{row["name"]}: {row["destination"]}' for row in legacy_conflicts)
        raise InstallError("legacy Skill path conflicts with safe migration: " + detail)

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
    _remove_matching_legacy_links(target_root, root=repo)

    for name, source in sources.items():
        destination = target_root / name
        if not destination.is_symlink():
            destination.symlink_to(source, target_is_directory=True)

    return inspect(target_root, root=repo)


def uninstall(target_root: Path, *, root: Optional[Path] = None) -> list[dict[str, str]]:
    repo = (root or repository_root()).resolve()
    sources = skill_sources(repo)
    target_root = target_root.expanduser()

    for name, source in sources.items():
        destination = target_root / name
        if _same_symlink(destination, source):
            destination.unlink()

    _remove_matching_legacy_links(target_root, root=repo)
    return inspect(target_root, root=repo)


def doctor(target_root: Path, *, root: Optional[Path] = None) -> dict[str, object]:
    repo = (root or repository_root()).resolve()
    version = project_version(repo)
    target_root = target_root.expanduser()
    rows = inspect(target_root, root=repo)
    legacy = _legacy_rows(target_root, root=repo)
    skill_checks: list[dict[str, object]] = []
    for row in rows:
        source = Path(row["source"])
        metadata = source / "agents" / "openai.yaml"
        skill_md = source / "SKILL.md"
        runtime_helper = source / "scripts" / "topic_radar_client.py"
        quality_contract = source / "references" / "quality-contract.md"
        selection_workflow = source / "references" / "selection-workflow.md"
        brief_workflow = source / "references" / "brief-workflow.md"
        check: dict[str, object] = {
            **row,
            "skill_md": "ok" if skill_md.is_file() else "missing",
            "openai_metadata": "ok" if metadata.is_file() else "missing",
            "runtime_helper": "ok" if runtime_helper.is_file() else "missing",
            "quality_contract": "ok" if quality_contract.is_file() else "missing",
            "selection_workflow": "ok" if selection_workflow.is_file() else "missing",
            "brief_workflow": "ok" if brief_workflow.is_file() else "missing",
        }
        check["ok"] = (
            row["state"] == "installed"
            and check["skill_md"] == "ok"
            and check["openai_metadata"] == "ok"
            and check["runtime_helper"] == "ok"
            and check["quality_contract"] == "ok"
            and check["selection_workflow"] == "ok"
            and check["brief_workflow"] == "ok"
        )
        skill_checks.append(check)

    legacy_clean = all(row["state"] == "missing" for row in legacy)
    python_ok = sys.version_info >= (3, 10)
    return {
        "name": "aiworkstation-topic-intelligence",
        "version": version,
        "repository_root": str(repo),
        "target_root": str(target_root),
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "python_supported": python_ok,
        "skills": skill_checks,
        "legacy_skills": legacy,
        "legacy_clean": legacy_clean,
        "ok": python_ok and legacy_clean and all(bool(item["ok"]) for item in skill_checks),
    }


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely install and diagnose Topic Intelligence Skills for Codex"
    )
    parser.add_argument(
        "command",
        choices=("install", "status", "doctor", "version", "uninstall"),
    )
    parser.add_argument(
        "--target-root",
        default=None,
        help="Override Codex Skill root (default: $HOME/.agents/skills)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    target_root = (
        Path(args.target_root).expanduser() if args.target_root else default_target_root()
    )

    try:
        if args.command == "install":
            payload: object = install(target_root)
        elif args.command == "uninstall":
            payload = uninstall(target_root)
        elif args.command == "doctor":
            payload = doctor(target_root)
        elif args.command == "version":
            payload = {
                "name": "aiworkstation-topic-intelligence",
                "version": project_version(),
            }
        else:
            payload = inspect(target_root)
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _print(payload)
    if args.command == "doctor" and isinstance(payload, dict) and not payload.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
