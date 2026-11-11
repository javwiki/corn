#!/usr/bin/env python3
"""Generate English navigation labels from page headings, preserving source paths."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = "# BEGIN GENERATED NAV"
END = "# END GENERATED NAV"


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def title(path: Path) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", path.read_text(), re.MULTILINE)
    if not match:
        raise ValueError(f"missing page heading: {path}")
    return match.group(1)


def navigation(root: Path) -> str:
    docs = root / "docs/en"
    lines = [START, "nav = [", '  { "Home" = "index.md" },']

    def directory(path: Path, indent: int) -> None:
        prefix = " " * indent
        index = path / "index.md"
        label = path.name if re.fullmatch(r"[A-Z]", path.name) else title(index)
        lines.append(f"{prefix}{{ {quoted(label)} = [")
        lines.append(f"{prefix}  {quoted(index.relative_to(docs).as_posix())},")
        for child in sorted(path.iterdir()):
            if child.is_dir():
                directory(child, indent + 2)
            elif child.suffix == ".md" and child.name != "index.md":
                relative = child.relative_to(docs).as_posix()
                lines.append(
                    f"{prefix}  {{ {quoted(title(child))} = {quoted(relative)} }},"
                )
        lines.append(f"{prefix}] }},")

    for category in ("人物", "作品", "资料", "专题"):
        directory(docs / category, 2)
    lines.extend(["]", END])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = ROOT / "zensical.toml"
    text = config.read_text()
    generated = navigation(ROOT)
    if START in text and END in text:
        updated = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            lambda _: generated,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        updated = text.replace("[project]\n", "[project]\n" + generated + "\n", 1)
    if args.check:
        if updated != text:
            print(
                "English navigation is out of date; run scripts/content/generate_navigation.py"
            )
            return 1
    else:
        config.write_text(updated)
    print(
        "English navigation check passed"
        if args.check
        else "English navigation generated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
