#!/usr/bin/env python3
"""Render bilingual work pages from source-attributed research and the original CSV."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {
    "official": ("官方目录资料", "Official catalog metadata"),
    "database": (
        "数据库资料，待发行方复核",
        "Database metadata; producer confirmation pending",
    ),
    "secondary": ("二手资料，待复核", "Secondary source; confirmation pending"),
    "trade_press": ("行业报道资料", "Trade press metadata"),
    "unresolved": ("待核实", "Unresolved"),
}
FIELDS = {
    "cast": ("演员", "Cast"),
    "credited_as": ("署名", "Credited as"),
    "label": ("发行平台／标签", "Release platform / label"),
    "series": ("系列", "Series"),
    "release": ("发布日期（来源所列精度）", "Release date (source precision)"),
    "reported": ("报道日期（非首发日期）", "Report date (not a release date)"),
    "runtime": ("片长（来源所列精度）", "Runtime (source precision)"),
    "director": ("导演", "Director"),
    "catalog_id": ("目录编号", "Catalog ID"),
}


def escape(value: str) -> str:
    return re.sub(r"([\\`*\[\]_|<>])", r"\\\1", value)


def load_research(root: Path) -> tuple[dict, list[dict]]:
    data = yaml.safe_load((root / "maintenance/works.yaml").read_text())
    with (root / data["source_csv"]).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or any(not row.get("Title") for row in rows):
        raise ValueError("source CSV must contain non-empty titles")
    covered: list[int] = []
    filenames: set[str] = set()
    identifiers: set[str] = set()
    if not data["items"]:
        raise ValueError("research must contain work records")
    for item in data["items"]:
        if not re.fullmatch(r"[A-Za-z0-9_]+\.md", item["file"]):
            raise ValueError("work filename must be a simple Markdown filename")
        if item["file"] in filenames or item["id"] in identifiers:
            raise ValueError("duplicate work filename or ID")
        filenames.add(item["file"])
        identifiers.add(item["id"])
        if item["status"] not in STATUSES or not item["source_rows"]:
            raise ValueError("invalid status or empty source row mapping")
        covered.extend(item["source_rows"])
        for source in item["sources"]:
            parsed = urlsplit(source["url"])
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("sources must use absolute HTTPS URLs")
        if item["status"] != "unresolved" and not item["sources"]:
            raise ValueError("a sourced record must have sources")
        seen_fields: set[str] = set()
        for field in item["fields"]:
            if field["key"] not in FIELDS or field["key"] in seen_fields:
                raise ValueError("unknown or duplicate metadata field")
            seen_fields.add(field["key"])
            if not isinstance(field["source"], int) or not (
                0 <= field["source"] < len(item["sources"])
            ):
                raise ValueError("each metadata field must cite an existing source")
            if field["key"] == "cast" and not isinstance(field["value"], list):
                raise ValueError("cast must be a list")
        if item["status"] == "unresolved" and item["fields"]:
            raise ValueError("unresolved records cannot assert researched metadata")
    if Counter(covered) != Counter(range(1, len(rows) + 1)):
        raise ValueError("every CSV row must map to exactly one work record")
    return data, rows


def actor_link(root: Path, lang: str, name: str) -> str:
    filename = name.replace(" ", "_") + ".md"
    relative = Path("人物/演员") / name[0].upper() / filename
    if (root / "docs" / lang / relative).exists():
        return f"[{escape(name)}](../../{relative.as_posix()})"
    return escape(name)


def render_page(root: Path, data: dict, rows: list[dict], item: dict, lang: str) -> str:
    zh = lang == "zh"
    col = 0 if zh else 1
    metadata = yaml.safe_dump(
        {
            "entity_type": "work",
            "work_id": item["id"],
            "research_status": item["status"],
            "source_rows": item["source_rows"],
        },
        sort_keys=False,
    ).strip()
    result = f"---\n{metadata}\n---\n\n# {escape(item['title'])}\n\n"
    result += f"**{'资料状态' if zh else 'Research status'}：** {STATUSES[item['status']][col]}\n\n"
    result += f"## {'作品资料' if zh else 'Metadata'}\n\n"
    if item["fields"]:
        result += (
            "| 字段 | 记录 | 出处 |\n| --- | --- | --- |\n"
            if zh
            else "| Field | Record | Source |\n| --- | --- | --- |\n"
        )
        for field in item["fields"]:
            value = (
                ", ".join(actor_link(root, lang, name) for name in field["value"])
                if field["key"] == "cast"
                else escape(str(field["value"]))
            )
            source = item["sources"][field["source"]]
            label = (
                f"出处 {field['source'] + 1}" if zh else f"Source {field['source'] + 1}"
            )
            result += f"| {FIELDS[field['key']][col]} | {value} | [{label}]({source['url']}) |\n"
    else:
        result += (
            "尚未取得可用的作品级出处。片名、演员、发行方、日期和片长均待核实；下列原始记录仅用于辨认，不作为已确认的作品资料。\n"
            if zh
            else "No usable title-level source was obtained. Title, cast, label, date and runtime remain unverified. The original record below is an identification lead, not confirmed metadata.\n"
        )
    result += f"\n## {'辨认与资料限制' if zh else 'Identification and source limits'}\n\n{item['notes'][lang]}\n"
    result += f"\n## {'原始清单记录' if zh else 'Original catalog record'}\n\n"
    for number in item["source_rows"]:
        result += f"{'记录' if zh else 'Record'} {number}\n\n```text\n{rows[number - 1]['Title']}\n```\n\n"
    result += f"## {'参考资料' if zh else 'Sources'}\n\n"
    for index, source in enumerate(item["sources"], 1):
        result += f"{index}. [{escape(source['label'])}]({source['url']})\n"
    repo = "https://github.com/javwiki/corn/blob/main/maintenance/scene.csv"
    result += f"\n- [{'仓库原始清单（未核实线索）' if zh else 'Original repository catalog (unverified leads)'}]({repo})\n"
    result += (
        f"\n{'资料检索日期' if zh else 'Research date'}：{data['researched_on']}\n\n"
    )
    result += "[返回作品目录](index.md)\n" if zh else "[Back to works](index.md)\n"
    return result


def render(root: Path, data: dict, rows: list[dict]) -> dict[Path, str]:
    result: dict[Path, str] = {}
    for lang in ("zh", "en"):
        zh = lang == "zh"
        base = root / "docs" / lang / "作品"
        heading = (
            "# 作品\n\n- [单部作品与场景](单部/index.md)\n"
            if zh
            else "# Works\n\n- [Individual works and scenes](单部/index.md)\n"
        )
        heading += (
            f"\n原清单 {len(rows)} 条记录已整理为 {len(data['items'])} 个独立资料页；两条 Cosmid 记录归于同一条目。各页注明已有出处和未核实部分。\n"
            if zh
            else f"\nThe {len(rows)} CSV records map to {len(data['items'])} separate research pages. Two Cosmid records share one entry. Each page distinguishes sourced metadata from unverified leads.\n"
        )
        result[base / "index.md"] = heading
        index = "# 单部作品与场景\n\n" if zh else "# Individual works and scenes\n\n"
        index += (
            "本目录包含已找到出处的作品和仍待辨认的记录；状态只说明现有资料来源，不代表作品的全部信息已核实。\n\n"
            if zh
            else "This directory includes sourced works and records still awaiting identification. Status describes the available evidence; it does not verify every fact about a work.\n\n"
        )
        index += (
            "| 作品／记录 | 资料状态 |\n| --- | --- |\n"
            if zh
            else "| Work / record | Research status |\n| --- | --- |\n"
        )
        for item in data["items"]:
            index += f"| [{escape(item['title'])}]({item['file']}) | {STATUSES[item['status']][0 if zh else 1]} |\n"
            result[base / "单部" / item["file"]] = render_page(
                root, data, rows, item, lang
            )
        result[base / "单部/index.md"] = index
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        data, rows = load_research(root)
        pages = render(root, data, rows)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"works generation failed: {exc}")
        return 1
    unexpected = sorted(
        str(path.relative_to(root))
        for lang in ("zh", "en")
        for path in (root / "docs" / lang / "作品/单部").rglob("*.md")
        if path not in pages
    )
    if unexpected:
        print("unmapped work pages must be reconciled:\n" + "\n".join(unexpected))
        return 1
    stale = []
    for path, text in pages.items():
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(str(path.relative_to(root)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if stale:
        print("work pages are out of date:\n" + "\n".join(stale))
        return 1
    print(
        f"works {'check' if args.check else 'generation'} passed ({len(data['items'])} entries; {len(rows)} CSV records)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
