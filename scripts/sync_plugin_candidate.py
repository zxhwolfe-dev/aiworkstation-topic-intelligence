#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "topic-intelligence"
TARGET = ROOT / "plugin-candidate" / "ai-topic-intelligence" / "skills" / "topic-intelligence"
IGNORED_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def relative_files(root: Path) -> list[Path]:
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    )


def is_synced() -> bool:
    if not TARGET.is_dir() or relative_files(SOURCE) != relative_files(TARGET):
        return False
    return all(filecmp.cmp(SOURCE / relative, TARGET / relative, shallow=False) for relative in relative_files(SOURCE))


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize the canonical Skill into the skills-only Plugin candidate.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not is_synced():
            raise SystemExit("Plugin candidate Skill is not synchronized")
        print("Plugin candidate Skill is synchronized")
        return 0
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=IGNORED_NAMES)
    print(f"Synchronized {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
