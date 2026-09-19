#!/usr/bin/env python3
"""Fail when the English and Chinese documentation trees drift apart."""

from pathlib import Path


def files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


zh = files(Path("docs/zh"))
en = files(Path("docs/en"))

missing_en = sorted(zh - en)
missing_zh = sorted(en - zh)

if missing_en or missing_zh:
    if missing_en:
        print("Missing from docs/en:")
        print(*(f"  {path}" for path in missing_en), sep="\n")
    if missing_zh:
        print("Missing from docs/zh:")
        print(*(f"  {path}" for path in missing_zh), sep="\n")
    raise SystemExit(1)

print(f"i18n trees match ({len(zh)} files per language)")
