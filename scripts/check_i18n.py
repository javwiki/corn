#!/usr/bin/env python3
"""Validate the bilingual documentation tree before it is built.

The validator deliberately has no network or build-time side effects.  It is
kept as a normal script (rather than a shell-only path comparison) so the same
checks are used by local builds and by CI.  The repository root is derived from
this file, which also makes ``python scripts/check_i18n.py`` work from any
working directory.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

try:  # PyYAML is locked as a direct project dependency.
    import yaml
except ImportError:  # pragma: no cover - the fallback keeps the script portable.
    yaml = None  # type: ignore[assignment]

YAML_ERRORS = (
    (ValueError, TypeError, SyntaxError, yaml.YAMLError)
    if yaml is not None
    else (ValueError, TypeError, SyntaxError)
)


LANGUAGES = ("zh", "en")
CANONICAL_SITE_ROOT = "https://javwiki.github.io/corn/"
CANONICAL_SITE_URLS = {
    "zh": CANONICAL_SITE_ROOT,
    "en": CANONICAL_SITE_ROOT + "en/",
}
CANONICAL_DOCS_DIRS = {lang: f"docs/{lang}" for lang in LANGUAGES}
CANONICAL_SITE_DIRS = {"zh": "site", "en": "site/en"}
CONFIG_FILES = {"zh": "zensical.toml", "en": "zensical.en.toml"}
ALLOWED_PROTOCOLS = {"https", "mailto", "tel"}
DANGEROUS_PROTOCOLS = {"http", "javascript", "vbscript", "data", "file", "about"}
SOCIAL_DOMAINS = {
    "x.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "youtu.be",
    "twitch.tv",
    "linktr.ee",
    "onlyfans.com",
    "fansly.com",
    "bsky.app",
}
HANDLE_RE = re.compile(r"(?<![\w])@([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_])?)")
PERCENT_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:%|per\s+cent|percent)\s*$", re.IGNORECASE
)
LIST_MD_RE = re.compile(
    r"^\s*-\s+\*\*(?P<name>[^*]+?)\*\*\s*"
    r"\((?P<index>[A-Za-z])\)\s*-\s*.*?"
    r"(?P<percent>\d+(?:\.\d+)?)\s*(?:%|per\s+cent|percent)\s*$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Link:
    label: str
    destination: str
    start: int
    end: int


@dataclass(frozen=True)
class Measurement:
    kind: str
    value: float


class Reporter:
    """Collect all failures so one run explains all broken contracts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []
        self._counts: dict[str, int] = {}
        self._suppressed: set[str] = set()

    def path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(path)

    def error(self, check: str, path: Path | str, message: str) -> None:
        location = self.path(path) if isinstance(path, Path) else path
        self.errors.append(f"[{check}] {location}: {message}")
        self._counts[check] = self._counts.get(check, 0) + 1

    def limit(self, check: str, maximum: int = 100) -> None:
        count = self._counts.get(check, 0)
        if count >= maximum and check not in self._suppressed:
            self.errors.append(
                f"[{check}] additional failures suppressed after {maximum} errors"
            )
            self._suppressed.add(check)

    def emit(self) -> None:
        if not self.errors:
            return
        print(f"documentation validation failed ({len(self.errors)} error(s)):")
        for error in self.errors:
            print(f"  - {error}")


def _fallback_scalar(value: str) -> Any:
    """Parse the small YAML scalar subset used by this repository."""

    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith(("[", "{")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+)", value):
        return float(value)
    return value


def _fallback_yaml(text: str) -> Any:
    """Load the deliberately simple metadata/frontmatter YAML subset.

    The locked environment uses PyYAML.  This fallback is only a convenience
    for a system Python invocation and supports the list-of-mappings and list
    of-scalars forms used by the content; unsupported constructs are rejected
    rather than silently ignored.
    """

    result: dict[str, Any] = {}
    current_list: list[Any] | None = None
    current_item: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        # YAML permits a list item at the same indentation as its parent key.
        # Handle it before the top-level mapping branch.
        if line.startswith("- ") and current_list is not None:
            item_text = line[2:].strip()
            if ":" in item_text:
                key, value = item_text.split(":", 1)
                current_item = {key.strip(): _fallback_scalar(value)}
                current_list.append(current_item)
            else:
                current_list.append(_fallback_scalar(item_text))
                current_item = None
            continue

        if indent == 0:
            if line.startswith("- ") or ":" not in line:
                raise ValueError(f"unsupported YAML line: {raw_line}")
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if key in result:
                raise ValueError(f"duplicate YAML key: {key}")
            if value:
                result[key] = _fallback_scalar(value)
                current_list = None
                current_item = None
            else:
                current_list = []
                result[key] = current_list
                current_item = None
            continue

        if current_list is None:
            raise ValueError(f"unexpected indented YAML: {raw_line}")
        if current_item is None or ":" not in line:
            raise ValueError(f"unsupported YAML list item: {raw_line}")
        key, value = line.split(":", 1)
        if key.strip() in current_item:
            raise ValueError(f"duplicate YAML key: {key.strip()}")
        current_item[key.strip()] = _fallback_scalar(value)
    return result


if yaml is not None:

    class _UniqueKeyLoader(yaml.SafeLoader):  # type: ignore[misc]
        """SafeLoader variant which does not silently overwrite duplicate keys."""

    def _construct_unique_mapping(
        loader: Any, node: Any, deep: bool = False
    ) -> dict[Any, Any]:
        loader.flatten_mapping(node)
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate YAML key: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    _UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_unique_mapping,
    )


def parse_yaml(text: str) -> Any:
    if yaml is not None:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    return _fallback_yaml(text)


def read_text(path: Path, reporter: Reporter) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        reporter.error("read", path, f"cannot read UTF-8 file: {exc}")
        return None


def files(root: Path) -> set[Path]:
    """Return tracked-style relative paths for a language tree.

    Keep this small compatibility helper from the original validator while
    using POSIX strings internally for deterministic comparisons.
    """

    return {Path(relative) for relative in relative_files(root)}


def relative_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def frontmatter_and_body(
    text: str, path: Path, reporter: Reporter
) -> tuple[dict[str, Any] | None, str]:
    """Return parsed frontmatter and the Markdown body.

    A missing frontmatter block is represented by ``None``.  If a block starts
    but never closes, an error is recorded and the original text is returned so
    the remaining checks can still provide useful diagnostics.
    """

    normalized = text.lstrip("\ufeff")
    lines = normalized.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, normalized
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        reporter.error(
            "frontmatter",
            path,
            "frontmatter starts with '---' but has no closing '---'",
        )
        return None, normalized
    raw = "".join(lines[1:closing])
    try:
        metadata = parse_yaml(raw)
    except YAML_ERRORS as exc:  # parser-specific exception types are not stable
        reporter.error("frontmatter", path, f"invalid YAML: {exc}")
        metadata = None
    if metadata is not None and not isinstance(metadata, dict):
        reporter.error("frontmatter", path, "frontmatter must be a YAML mapping")
        metadata = None
    body = "".join(lines[closing + 1 :])
    first_content_line = next(
        (line.strip() for line in body.splitlines() if line.strip()),
        "",
    )
    if first_content_line == "---":
        reporter.error(
            "frontmatter", path, "unexpected second '---' immediately after frontmatter"
        )
    return metadata, body


def actor_files(language_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(language_root.rglob("*.md")):
        relative = path.relative_to(language_root)
        if (
            len(relative.parts) != 2
            or relative.parts[0] == "_meta"
            or relative.name == "index.md"
        ):
            continue
        result[relative.as_posix()] = path
    return result


def is_actor_path(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    return (
        len(parts) == 2
        and parts[0] != "_meta"
        and parts[1].endswith(".md")
        and parts[1] != "index.md"
    )


def parse_percent(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        value = str(value)
    if not isinstance(value, str):
        return None
    match = PERCENT_RE.match(value)
    return float(match.group(1)) if match else None


def markdown_heading(text: str) -> str | None:
    match = H1_RE.search(text)
    return match.group(1).strip() if match else None


def mask_code(text: str) -> str:
    """Blank code spans/fences while retaining offsets and line structure."""

    lines = text.splitlines(keepends=True)
    output: list[str] = []
    fence: str | None = None
    for line in lines:
        stripped = line.lstrip()
        fence_match = re.match(r"(`{3,}|~{3,})", stripped)
        if fence is not None:
            output.append("".join("\n" if char == "\n" else " " for char in line))
            if fence_match and stripped.startswith(fence[0] * len(fence)):
                fence = None
            continue
        if fence_match:
            fence = fence_match.group(1)
            output.append("".join("\n" if char == "\n" else " " for char in line))
            continue
        # Inline code spans may contain arbitrary punctuation which should not
        # be interpreted as Markdown or HTML.
        line_out: list[str] = []
        index = 0
        while index < len(line):
            if line[index] != "`":
                line_out.append(line[index])
                index += 1
                continue
            run_end = index
            while run_end < len(line) and line[run_end] == "`":
                run_end += 1
            run = line[index:run_end]
            closing = line.find(run, run_end)
            if closing < 0:
                line_out.append(run)
                index = run_end
                continue
            line_out.append(
                "".join(
                    "\n" if char == "\n" else " "
                    for char in line[index : closing + len(run)]
                )
            )
            index = closing + len(run)
        output.append("".join(line_out))
    return "".join(output)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def split_link_destination(raw: str) -> tuple[str | None, str | None]:
    raw = raw.strip()
    if not raw:
        return None, "empty link destination"
    if raw.startswith("<"):
        end = raw.find(">")
        if end < 0:
            return None, "unclosed angle-bracket link destination"
        destination = raw[1:end]
        remainder = raw[end + 1 :].strip()
        if remainder and not re.match(r"^(?:\"[^\"]*\"|'[^']*'|\([^)]*\))$", remainder):
            return None, "invalid text after angle-bracket link destination"
        destination = destination.strip()
        return (destination or None), (
            "empty link destination" if not destination else None
        )
    # Literal whitespace is not valid in an unquoted Markdown destination.  A
    # quoted title is valid after the destination.
    match = re.match(r"^(\S+)(?:\s+(.*))?$", raw, re.DOTALL)
    if not match:
        return None, "malformed link destination"
    destination = match.group(1)
    title = (match.group(2) or "").strip()
    if title and not re.match(r"^(?:\"[^\"]*\"|'[^']*'|\([^)]*\))$", title):
        return None, "malformed link title"
    return destination, None


def find_closing_square(text: str, opening: int) -> int | None:
    depth = 0
    index = opening
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def find_closing_paren(text: str, opening: int) -> int | None:
    depth = 1
    index = opening + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def extract_inline_links(text: str) -> tuple[list[Link], list[tuple[int, str]]]:
    links: list[Link] = []
    malformed: list[tuple[int, str]] = []
    index = 0
    while index < len(text):
        if text[index] == "[" and (index == 0 or text[index - 1] != "\\"):
            closing_square = find_closing_square(text, index)
            if closing_square is None:
                malformed.append((index, "unclosed Markdown link label"))
                index += 1
                continue
            if closing_square + 1 < len(text) and text[closing_square + 1] == "(":
                closing_paren = find_closing_paren(text, closing_square + 1)
                if closing_paren is None:
                    malformed.append((index, "unclosed Markdown link destination"))
                    index = closing_square + 2
                    continue
                label = text[index + 1 : closing_square]
                raw_destination = text[closing_square + 2 : closing_paren]
                destination, error = split_link_destination(raw_destination)
                if error:
                    malformed.append((index, error))
                elif destination is not None:
                    links.append(
                        Link(
                            label=label,
                            destination=destination,
                            start=index,
                            end=closing_paren + 1,
                        )
                    )
                index = closing_paren + 1
                continue
        index += 1
    return links, malformed


def normalise_handle(handle: str) -> str:
    handle = unquote(handle).strip().lstrip("@")
    handle = handle.rstrip(".,;:!?)]}")
    return handle.casefold()


def url_handle(destination: str) -> tuple[str, str] | None:
    try:
        parsed = urlsplit(destination)
    except ValueError:
        return None
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    if host not in SOCIAL_DOMAINS:
        return None
    segments = [unquote(segment) for segment in parsed.path.split("/") if segment]
    if not segments:
        return None
    if (
        host == "bsky.app"
        and segments[0].casefold() == "profile"
        or host == "youtube.com"
        and segments[0].casefold() == "c"
    ):
        if len(segments) < 2:
            return None
        handle = segments[1]
    else:
        handle = segments[0]
    handle = handle.lstrip("@")
    if not handle or handle.casefold() in {"i", "c", "channel", "user"}:
        return None
    return host, normalise_handle(handle)


def protocol_error(destination: str) -> str | None:
    compact = re.sub(r"[\x00-\x20]+", "", destination).casefold()
    match = re.match(r"^([a-z][a-z0-9+.-]*):", compact)
    if not match:
        return None
    scheme = match.group(1)
    if scheme in DANGEROUS_PROTOCOLS:
        return f"dangerous URL protocol '{scheme}:'"
    if scheme not in ALLOWED_PROTOCOLS:
        return f"unsupported URL protocol '{scheme}:'"
    return None


def heading_slugs(text: str) -> set[str]:
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    for match in HEADING_RE.finditer(text):
        heading = re.sub(r"[`*_~]", "", match.group(1)).strip().casefold()
        heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
        heading = re.sub(r"\s+", "-", heading).strip("-")
        if not heading:
            continue
        count = counts.get(heading, 0)
        counts[heading] = count + 1
        slugs.add(heading if count == 0 else f"{heading}-{count}")
    return slugs


def check_destination(
    path: Path,
    link: Link,
    language_root: Path,
    reporter: Reporter,
) -> None:
    destination = link.destination
    error = protocol_error(destination)
    if error:
        reporter.error("security", path, f"{error} in Markdown link {destination!r}")
        return
    if any(char in destination for char in "\r\n"):
        reporter.error("links", path, "Markdown link destination contains a newline")
        return
    if destination.startswith("//"):
        reporter.error(
            "links", path, f"protocol-relative URL is not allowed: {destination!r}"
        )
        return
    if destination.startswith("#"):
        current_text = read_text(path, reporter)
        fragment = unquote(destination[1:]).casefold()
        if (
            current_text is not None
            and fragment
            and fragment not in heading_slugs(current_text)
        ):
            reporter.error(
                "links", path, f"local link fragment does not exist: {destination!r}"
            )
        return
    try:
        parsed = urlsplit(destination)
    except ValueError as exc:
        reporter.error("links", path, f"malformed URL {destination!r}: {exc}")
        return
    if parsed.scheme:
        if parsed.scheme.casefold() not in ALLOWED_PROTOCOLS:
            return
        if parsed.scheme.casefold() == "https":
            if not parsed.netloc:
                reporter.error("links", path, f"URL has no host: {destination!r}")
                return
            host = (parsed.hostname or "").casefold().removeprefix("www.")
            if host == "iafd.com" and parsed.path in {"", "/"}:
                reporter.error(
                    "sources",
                    path,
                    f"IAFD entry must link to a specific person page, not the site homepage: {destination!r}",
                )
            if host == "en.wikipedia.org" and parsed.path.startswith("/wiki/Draft:"):
                reporter.error(
                    "sources",
                    path,
                    f"rejected/unsubmitted Wikipedia Draft is not acceptable evidence: {destination!r}",
                )
        return

    raw_path = unquote(parsed.path)
    if not raw_path:
        return
    if "\\" in raw_path:
        reporter.error(
            "paths", path, f"Markdown link uses a backslash path: {destination!r}"
        )
        return
    if ".." in PurePosixPath(raw_path).parts:
        reporter.error(
            "paths", path, f"Markdown link uses a parent path segment: {destination!r}"
        )
        return
    target = (path.parent / raw_path).resolve()
    try:
        target.relative_to(language_root.resolve())
    except ValueError:
        reporter.error(
            "links", path, f"local link escapes the language tree: {destination!r}"
        )
        return
    if not target.exists():
        reporter.error(
            "links", path, f"local link target does not exist: {destination!r}"
        )
        return
    if target.is_dir():
        index_target = target / "index.md"
        if not index_target.exists():
            reporter.error(
                "links", path, f"directory link has no index.md: {destination!r}"
            )
            return
        target = index_target
    if parsed.fragment:
        target_text = read_text(target, reporter)
        if target_text is not None and unquote(
            parsed.fragment
        ).casefold() not in heading_slugs(target_text):
            reporter.error(
                "links", path, f"local link fragment does not exist: {destination!r}"
            )


def check_markdown_links_and_security(
    path: Path,
    body: str,
    language_root: Path,
    reporter: Reporter,
) -> list[Link]:
    masked = mask_code(body)
    links, malformed = extract_inline_links(masked)
    for match in re.finditer(r"\]\s+\(", masked):
        malformed.append(
            (match.start(), "whitespace between Markdown link label and destination")
        )
    for offset, message in malformed:
        reporter.error("links", path, f"{message} (line {line_number(masked, offset)})")
        reporter.limit("links")

    raw_html = re.compile(r"<!--|<\s*/?\s*[A-Za-z][^>]*>|<\s*[!?][^>]*>", re.IGNORECASE)
    for match in raw_html.finditer(masked):
        token = match.group(0)
        if re.fullmatch(r"<\s*(?:https?://|mailto:|tel:)[^>]+>", token, re.IGNORECASE):
            continue
        reporter.error(
            "security",
            path,
            f"raw HTML is not allowed: {token[:100]!r} (line {line_number(masked, match.start())})",
        )
        reporter.limit("security")

    for match in re.finditer(r"<\s*/?\s*[A-Za-z][^>\n]*$", masked, re.MULTILINE):
        reporter.error(
            "security", path, f"unclosed raw HTML tag: {match.group(0)[:100]!r}"
        )
        reporter.limit("security")

    for match in re.finditer(r"\bon[a-z][\w:-]*\s*=", masked, re.IGNORECASE):
        reporter.error(
            "security",
            path,
            f"event attribute is not allowed: {match.group(0).strip()} (line {line_number(masked, match.start())})",
        )
        reporter.limit("security")

    dangerous = re.compile(
        r"(?<![\w])(?:javascript|vbscript|data|file|about)\s*:", re.IGNORECASE
    )
    for match in dangerous.finditer(masked):
        reporter.error(
            "security",
            path,
            f"dangerous protocol is not allowed: {match.group(0)} (line {line_number(masked, match.start())})",
        )
        reporter.limit("security")

    # A dollar sign is interpreted by the Markdown math extensions unless it
    # is escaped.  Code spans/fences have already been masked.
    reported_dollar_lines: set[int] = set()
    for match in re.finditer(r"(?<!\\)\$", masked):
        current_line = line_number(masked, match.start())
        if current_line in reported_dollar_lines:
            continue
        reported_dollar_lines.add(current_line)
        reporter.error(
            "markdown", path, f"unescaped '$' (line {current_line}); write '\\$'"
        )
        reporter.limit("markdown")

    # Numeric markers in the form ``^[1]`` were emitted by the historical
    # translation script but have no definitions and render as literal text.
    # Proper Markdown footnotes use ``[^1]`` and are deliberately rejected
    # here until this project has a documented citation-rendering policy.
    for match in re.finditer(r"\^\[\d+\](?:\[\d+\])*", masked):
        reporter.error(
            "markdown",
            path,
            f"undefined numeric citation marker {match.group(0)!r} (line {line_number(masked, match.start())})",
        )
        reporter.limit("markdown")

    for link in links:
        check_destination(path, link, language_root, reporter)

    # Reference-link definitions are links too, and are not returned by the
    # inline-link parser.
    definitions: dict[str, str] = {}
    for match in re.finditer(r"(?m)^\s{0,3}\[([^\]]+)\]:\s*(\S+)", masked):
        label = match.group(1).strip().casefold()
        destination = match.group(2).strip()
        if label in definitions:
            reporter.error(
                "links", path, f"duplicate Markdown reference definition: {label}"
            )
        definitions[label] = destination
        error = protocol_error(destination)
        if error:
            reporter.error(
                "security", path, f"{error} in reference link {destination!r}"
            )
            continue
        if destination.startswith("#"):
            continue
        try:
            is_external = bool(urlsplit(destination).scheme)
        except ValueError as exc:
            reporter.error(
                "links", path, f"malformed reference URL {destination!r}: {exc}"
            )
            continue
        if is_external:
            continue
        check_destination(
            path,
            Link(
                label=label,
                destination=destination,
                start=match.start(),
                end=match.end(),
            ),
            language_root,
            reporter,
        )

    # Explicit reference links ([text][id]) must have a definition.  Citation
    # markers prefixed with ``^`` are left to the content convention and are
    # not treated as ordinary Markdown reference links.
    for match in re.finditer(r"(?<![!^])\[([^\]\n]+)\]\[([^\]\n]*)\]", masked):
        if re.search(r"\^\[[^\]]+\](?:\[[^\]]+\])*\s*$", masked[: match.start()]):
            continue
        reference = (match.group(2) or match.group(1)).strip().casefold()
        if reference not in definitions:
            reporter.error(
                "links",
                path,
                f"Markdown reference link has no definition: {match.group(0)!r}",
            )
            reporter.limit("links")
    return links


def check_handles(
    path: Path, body: str, links: Iterable[Link], reporter: Reporter
) -> set[tuple[str, str]]:
    masked = mask_code(body)
    pairs: set[tuple[str, str]] = set()
    for link in links:
        target = url_handle(link.destination)
        if target is None:
            continue
        _domain, url_name = target
        pairs.add(target)
        label_handles = {
            normalise_handle(value) for value in HANDLE_RE.findall(link.label)
        }
        if label_handles and url_name not in label_handles:
            reporter.error(
                "handles",
                path,
                f"link label handle(s) {sorted(label_handles)} do not match {link.destination!r} ({url_name})",
            )

    # Also compare a simple prose/table line such as `@name` next to one
    # social URL.  Lines containing multiple accounts are compared by the
    # link-level rule above to avoid pairing the wrong account.
    for line_number_value, line in enumerate(masked.splitlines(), 1):
        handles = {normalise_handle(value) for value in HANDLE_RE.findall(line)}
        candidates: list[tuple[str, str]] = []
        for url in re.findall(r"https?://[^\s<>()]+", line):
            target = url_handle(url.rstrip(".,;!?"))
            if target is not None:
                candidates.append(target)
        if len(handles) == 1 and len(candidates) == 1:
            expected = next(iter(handles))
            actual = candidates[0][1]
            if expected != actual:
                reporter.error(
                    "handles",
                    path,
                    f"@{expected} does not match {candidates[0][0]} URL handle @{actual} (line {line_number_value})",
                )
    return pairs


def extract_measurements(text: str) -> list[Measurement]:
    """Return canonical metric/percentage measurements from prose.

    The comparison is intentionally semantic: ``95 per cent`` and ``95%`` are
    equal, and common metric/imperial spellings are converted to one canonical
    unit before the bilingual pages are compared.
    """

    text = mask_code(text)
    measurements: list[Measurement] = []
    occupied: list[tuple[int, int]] = []
    composite = re.compile(
        r"(?<![\d.])(\d+)\s*(?:feet|foot|ft|'|尺)\s*"
        r"(\d+(?:\.\d+)?)?\s*(?:inches|inch|in|\"|寸)",
        re.IGNORECASE,
    )
    for match in composite.finditer(text):
        feet = int(match.group(1))
        inches = float(match.group(2) or 0)
        measurements.append(Measurement("height", feet * 30.48 + inches * 2.54))
        occupied.append(match.span())

    def overlaps(start: int, end: int) -> bool:
        return any(
            start < old_end and end > old_start for old_start, old_end in occupied
        )

    simple = re.compile(
        r"(?<![\d.])(\d+(?:\.\d+)?)\s*"
        r"(cm|厘米|m|米|kg|公斤|千克|lbs?|pounds?|磅|inches|inch|in|寸|feet|foot|ft|尺|per\s+cent|percent|%)"
        r"(?![\w])",
        re.IGNORECASE,
    )
    for match in simple.finditer(text):
        if overlaps(*match.span()):
            continue
        value = float(match.group(1))
        unit = re.sub(r"\s+", "", match.group(2)).casefold()
        if unit in {"cm", "厘米"}:
            measurements.append(Measurement("height", value))
        elif unit in {"m", "米"}:
            measurements.append(Measurement("height", value * 100))
        elif unit in {"kg", "公斤", "千克"}:
            measurements.append(Measurement("mass", value))
        elif unit in {"lb", "lbs", "pound", "pounds", "磅"}:
            measurements.append(Measurement("mass", value * 0.45359237))
        elif unit in {"in", "inch", "inches", "寸"}:
            measurements.append(Measurement("height", value * 2.54))
        elif unit in {"ft", "foot", "feet", "尺"}:
            measurements.append(Measurement("height", value * 30.48))
        else:
            measurements.append(Measurement("percent", value))
    return measurements


def close_measurement(left: float, right: float, kind: str) -> bool:
    tolerance = 1.5 if kind == "height" else 0.5 if kind == "mass" else 0.01
    return abs(left - right) <= tolerance


def chinese_magnitude_counts(text: str) -> Counter[float]:
    """Normalize Chinese 万/亿 quantities to their integer magnitude."""

    counts: Counter[float] = Counter()
    for match in re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*(万|亿)(?!\d)", text):
        multiplier = 10_000 if match.group(2) == "万" else 100_000_000
        counts[round(float(match.group(1)) * multiplier, 6)] += 1
    return counts


def english_magnitude_counts(text: str) -> Counter[float]:
    """Collect large English quantities for comparison with 万/亿 values.

    This accepts full words (``2.6 million``), compact suffixes (``2.6M``),
    comma-grouped integers (``2,600,000``), and plain integers of at least
    10,000. Years and ordinary small counts are intentionally ignored.
    """

    text = re.sub(r"https?://\S+", " ", mask_code(text))
    counts: Counter[float] = Counter()
    suffix_multipliers = {
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
    }
    occupied: list[tuple[int, int]] = []
    for match in re.finditer(
        r"(?<![\w.])(\d+(?:\.\d+)?)\s*(thousand|million|billion|[KMB])(?![A-Za-z])",
        text,
        re.IGNORECASE,
    ):
        counts[
            round(
                float(match.group(1)) * suffix_multipliers[match.group(2).casefold()], 6
            )
        ] += 1
        occupied.append(match.span())
    for match in re.finditer(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?!\w)", text):
        counts[float(match.group(0).replace(",", ""))] += 1
        occupied.append(match.span())
    # Replace commas with spaces rather than deleting them so offsets from the
    # suffix pass remain comparable.
    plain_text = text.replace(",", " ")
    for match in re.finditer(r"(?<![\w.])\d{4,}(?:\.\d+)?(?![\w])", plain_text):
        if any(match.start() < end and match.end() > start for start, end in occupied):
            continue
        value = float(match.group(0))
        if value >= 10_000:
            counts[value] += 1
    return counts


def first_labeled_measurements(text: str, labels: Iterable[str]) -> list[Measurement]:
    label_patterns = [
        rf"(?:\*\*{re.escape(label)}\*\*|^\s*[-|]?\s*{re.escape(label)}\s*:|\|\s*{re.escape(label)}\s*\|)"
        for label in labels
    ]
    for line in text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in label_patterns):
            return [
                item
                for item in extract_measurements(line)
                if item.kind in {"height", "mass"}
            ]
    return []


def first_labeled_count(text: str, labels: Iterable[str]) -> int | None:
    label_patterns = [
        rf"(?:\*\*{re.escape(label)}\*\*|^\s*[-|]?\s*{re.escape(label)}\s*:|\|\s*{re.escape(label)}\s*\|)"
        for label in labels
    ]
    spelled_numbers = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
    }
    for line in text.splitlines():
        if not any(
            re.search(pattern, line, re.IGNORECASE) for pattern in label_patterns
        ):
            continue
        value = re.split(r"[:：]", line, maxsplit=1)[-1]
        first_word = re.search(r"[A-Za-z]+", value)
        first_number = re.search(r"(?<![A-Za-z])\d[\d,]*(?!\d)", value)
        if first_word and (
            first_number is None or first_word.start() < first_number.start()
        ):
            word = first_word.group(0).casefold()
            if word in spelled_numbers:
                return spelled_numbers[word]
        match = first_number
        return int(match.group(0).replace(",", "")) if match else None
    return None


def check_bilingual_measurements(
    actor_paths: dict[str, dict[str, Path]],
    reporter: Reporter,
) -> None:
    common = sorted(set(actor_paths["zh"]) & set(actor_paths["en"]))
    for relative in common:
        zh_path = actor_paths["zh"][relative]
        en_path = actor_paths["en"][relative]
        zh_text = read_text(zh_path, reporter) or ""
        en_text = read_text(en_path, reporter) or ""
        missing_magnitudes = chinese_magnitude_counts(
            zh_text
        ) - english_magnitude_counts(en_text)
        if missing_magnitudes:
            reporter.error(
                "units",
                zh_path,
                "万/亿 quantities are missing or changed in "
                f"{reporter.path(en_path)}: {dict(missing_magnitudes)}",
            )
            reporter.limit("units")
        for kind, zh_labels, en_labels in (
            ("height", ("身高",), ("Height",)),
            ("mass", ("体重",), ("Weight",)),
        ):
            zh_values = [
                item.value
                for item in first_labeled_measurements(zh_text, zh_labels)
                if item.kind == kind
            ]
            en_values = [
                item.value
                for item in first_labeled_measurements(en_text, en_labels)
                if item.kind == kind
            ]
            if (
                zh_values
                and en_values
                and not any(
                    close_measurement(left, right, kind)
                    for left in zh_values
                    for right in en_values
                )
            ):
                reporter.error(
                    "units",
                    zh_path,
                    f"{kind} does not match {reporter.path(en_path)} after unit normalization: {zh_values} vs {en_values}",
                )
                reporter.limit("units")

        zh_count = first_labeled_count(zh_text, ("作品数量",))
        en_count = first_labeled_count(en_text, ("Number of works",))
        if zh_count is not None and en_count is not None and zh_count != en_count:
            reporter.error(
                "units",
                zh_path,
                f"work count does not match {reporter.path(en_path)}: {zh_count} vs {en_count}",
            )
            reporter.limit("units")

        zh_percent = sorted(
            item.value
            for item in extract_measurements(zh_text)
            if item.kind == "percent"
        )
        en_percent = sorted(
            item.value
            for item in extract_measurements(en_text)
            if item.kind == "percent"
        )
        if zh_percent and en_percent and zh_percent != en_percent:
            reporter.error(
                "units",
                zh_path,
                f"percentage values do not match {reporter.path(en_path)} after normalization: {zh_percent} vs {en_percent}",
            )
            reporter.limit("units")


def check_config_contracts(root: Path, reporter: Reporter) -> None:
    projects: dict[str, dict[str, Any]] = {}
    for lang, filename in CONFIG_FILES.items():
        path = root / filename
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            reporter.error("config", path, f"cannot load TOML: {exc}")
            continue
        project = data.get("project")
        if not isinstance(project, dict):
            reporter.error("config", path, "missing [project] table")
            continue
        projects[lang] = project
        for key in ("docs_dir", "site_dir", "site_url"):
            if not isinstance(project.get(key), str) or not project[key]:
                reporter.error(
                    "config", path, f"project.{key} must be a non-empty string"
                )
        if project.get("docs_dir") != CANONICAL_DOCS_DIRS[lang]:
            reporter.error(
                "config",
                path,
                f"project.docs_dir must be {CANONICAL_DOCS_DIRS[lang]!r}, got {project.get('docs_dir')!r}",
            )
        if project.get("site_dir") != CANONICAL_SITE_DIRS[lang]:
            reporter.error(
                "config",
                path,
                f"project.site_dir must be {CANONICAL_SITE_DIRS[lang]!r}, got {project.get('site_dir')!r}",
            )
        if project.get("site_url") != CANONICAL_SITE_URLS[lang]:
            reporter.error(
                "config",
                path,
                f"project.site_url must be {CANONICAL_SITE_URLS[lang]!r}, got {project.get('site_url')!r}",
            )
        if project.get("use_directory_urls") is not True:
            reporter.error(
                "config",
                path,
                "project.use_directory_urls must remain true for the nested site/en layout",
            )
        theme = project.get("theme")
        if not isinstance(theme, dict) or theme.get("custom_dir") != "overrides":
            reporter.error(
                "config",
                path,
                "project.theme.custom_dir must remain 'overrides' for the bilingual 404 template",
            )
        if not isinstance(theme, dict) or theme.get("font") is not False:
            reporter.error(
                "config",
                path,
                "project.theme.font must be false to avoid third-party font requests",
            )
        alternate = (
            project.get("extra", {}).get("alternate")
            if isinstance(project.get("extra"), dict)
            else None
        )
        expected_alternate = [
            {"name": "中文", "link": "/corn/", "lang": "zh"},
            {"name": "English", "link": "/corn/en/", "lang": "en"},
        ]
        if alternate != expected_alternate:
            reporter.error(
                "config",
                path,
                "project.extra.alternate does not describe the zh/en site contract",
            )

    override = root / "overrides" / "404.html"
    override_text = read_text(override, reporter)
    if override_text is not None:
        for required in ("页面未找到", "Page not found", "config.extra.alternate"):
            if required not in override_text:
                reporter.error(
                    "config",
                    override,
                    f"bilingual 404 template is missing {required!r}",
                )
    for relative, required in (
        ("overrides/main.html", ("page.url", "alt.link")),
        ("overrides/partials/alternate.html", ("page.url", "alt.link")),
    ):
        template = root / relative
        template_text = read_text(template, reporter)
        if template_text is not None:
            for marker in required:
                if marker not in template_text:
                    reporter.error(
                        "config",
                        template,
                        f"page-level language template is missing {marker!r}",
                    )

    if "zh" in projects and "en" in projects:
        zh_url = projects["zh"].get("site_url")
        en_url = projects["en"].get("site_url")
        if (
            isinstance(zh_url, str)
            and isinstance(en_url, str)
            and (not en_url.startswith(zh_url) or not en_url.endswith("/"))
        ):
            reporter.error(
                "config",
                root / CONFIG_FILES["en"],
                "English site_url must be a child URL of the Chinese site_url",
            )
        zh_site = PurePosixPath(str(projects["zh"].get("site_dir", "")))
        en_site = PurePosixPath(str(projects["en"].get("site_dir", "")))
        if en_site != zh_site / "en":
            reporter.error(
                "config",
                root / CONFIG_FILES["en"],
                "English site_dir must be nested below the Chinese site_dir as <site_dir>/en",
            )


def load_list(root: Path, lang: str, reporter: Reporter) -> dict[str, Any] | None:
    path = root / "docs" / lang / "_meta" / "list.yaml"
    text = read_text(path, reporter)
    if text is None:
        return None
    try:
        data = parse_yaml(text)
    except YAML_ERRORS as exc:
        reporter.error("metadata", path, f"invalid YAML: {exc}")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        reporter.error("metadata", path, "expected a mapping with an items list")
        return None
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        reporter.error("metadata", path, "list.yaml must define a non-empty title")
    return data


def normalise_list_entry(
    entry: Any, path: Path, index: int, reporter: Reporter
) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        reporter.error("metadata", path, f"items[{index}] must be a mapping")
        return None
    result = dict(entry)
    for key in ("name", "file", "index", "completeness"):
        if key not in result:
            reporter.error("metadata", path, f"items[{index}] is missing {key}")
    name = result.get("name")
    filename = result.get("file")
    index_value = result.get("index")
    percent = parse_percent(result.get("completeness"))
    if not isinstance(name, str) or not name.strip():
        reporter.error("metadata", path, f"items[{index}].name must be non-empty")
    if (
        not isinstance(filename, str)
        or not filename.endswith(".md")
        or filename.startswith("/")
        or "\\" in filename
    ):
        reporter.error(
            "metadata", path, f"items[{index}].file must be a relative Markdown path"
        )
    if (
        not isinstance(index_value, str)
        or len(index_value) != 1
        or not index_value.isascii()
        or not index_value.isalpha()
        or not index_value.isupper()
    ):
        reporter.error(
            "metadata", path, f"items[{index}].index must be one uppercase ASCII letter"
        )
    if percent is None or not 0 <= percent <= 100:
        reporter.error(
            "metadata",
            path,
            f"items[{index}].completeness must be a percentage from 0% to 100%",
        )
    if isinstance(filename, str):
        pure = PurePosixPath(filename)
        if pure.is_absolute() or ".." in pure.parts or len(pure.parts) != 2:
            reporter.error(
                "metadata", path, f"items[{index}].file must be <letter>/<name>.md"
            )
    if isinstance(name, str) and isinstance(index_value, str) and name.strip():
        first = next(
            (
                char
                for char in name.strip()
                if unicodedata.category(char).startswith("L")
            ),
            "",
        )
        if not first or first.upper() != index_value.upper():
            reporter.error(
                "metadata",
                path,
                f"items[{index}] name {name!r} does not start with index {index_value!r}",
            )
        if isinstance(filename, str):
            expected_stem = name.strip().replace(" ", "_")
            if PurePosixPath(filename).stem != expected_stem:
                reporter.error(
                    "metadata",
                    path,
                    f"items[{index}].file does not match name {name!r}",
                )
    result["_percent"] = percent
    return result


def check_lists(
    root: Path, languages: dict[str, Path], reporter: Reporter
) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    lists: dict[str, dict[str, Any]] = {}
    list_files: dict[str, set[str]] = {}
    for lang, language_root in languages.items():
        data = load_list(root, lang, reporter)
        if data is None:
            lists[lang] = {"items": []}
            list_files[lang] = set()
            continue
        normalised: list[dict[str, Any]] = []
        files: set[str] = set()
        names: set[str] = set()
        for index, entry in enumerate(data["items"]):
            item = normalise_list_entry(
                entry, language_root / "_meta" / "list.yaml", index, reporter
            )
            if item is None:
                continue
            filename = item.get("file")
            if isinstance(filename, str):
                if filename in files:
                    reporter.error(
                        "metadata",
                        language_root / "_meta" / "list.yaml",
                        f"duplicate list file: {filename}",
                    )
                files.add(filename)
            name_key = str(item.get("name", "")).casefold()
            if name_key in names:
                reporter.error(
                    "metadata",
                    language_root / "_meta" / "list.yaml",
                    f"duplicate list name: {item.get('name')}",
                )
            names.add(name_key)
            normalised.append(item)
        lists[lang] = {**data, "items": normalised}
        list_files[lang] = files
        actual = set(actor_files(language_root))
        missing = sorted(actual - files)
        extra = sorted(files - actual)
        list_path = language_root / "_meta" / "list.yaml"
        for filename in missing:
            reporter.error(
                "metadata",
                list_path,
                f"actor page is missing from list.yaml: {filename}",
            )
        for filename in extra:
            reporter.error(
                "metadata",
                list_path,
                f"list.yaml references a non-actor page: {filename}",
            )
    if "zh" in lists and "en" in lists:
        zh = {item.get("file"): item for item in lists["zh"].get("items", [])}
        en = {item.get("file"): item for item in lists["en"].get("items", [])}
        for filename in sorted(set(zh) | set(en)):
            if filename not in zh or filename not in en:
                continue
            for key in ("name", "index", "_percent"):
                if zh[filename].get(key) != en[filename].get(key):
                    reporter.error(
                        "metadata",
                        root / "docs" / "en" / "_meta" / "list.yaml",
                        f"{filename} differs between languages for {key}",
                    )
    return lists, list_files


def parse_list_md(path: Path, reporter: Reporter) -> dict[str, dict[str, Any]]:
    text = read_text(path, reporter)
    if text is None:
        return {}
    if not HEADING_RE.search(text):
        reporter.error("metadata", path, "list.md must start with a Markdown heading")
    entries: dict[str, dict[str, Any]] = {}
    for line_number_value, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = LIST_MD_RE.match(line)
        if not match:
            reporter.error(
                "metadata", path, f"line {line_number_value} is not a valid list entry"
            )
            continue
        name = match.group("name").strip()
        key = name.casefold()
        if key in entries:
            reporter.error("metadata", path, f"duplicate list.md entry: {name}")
        entries[key] = {
            "name": name,
            "index": match.group("index").upper(),
            "percent": float(match.group("percent")),
        }
    if not entries:
        reporter.error("metadata", path, "list.md contains no entries")
    return entries


def check_list_md(
    root: Path,
    languages: dict[str, Path],
    lists: dict[str, dict[str, Any]],
    reporter: Reporter,
) -> None:
    parsed: dict[str, dict[str, dict[str, Any]]] = {}
    for lang, language_root in languages.items():
        path = language_root / "_meta" / "list.md"
        parsed[lang] = parse_list_md(path, reporter)
        by_name = {
            str(item.get("name", "")).casefold(): item
            for item in lists.get(lang, {}).get("items", [])
        }
        for key, entry in parsed[lang].items():
            source = by_name.get(key)
            if source is None:
                reporter.error(
                    "metadata",
                    path,
                    f"list.md entry {entry['name']!r} is not in list.yaml",
                )
                continue
            if entry["index"] != source.get("index"):
                reporter.error(
                    "metadata", path, f"{entry['name']} index differs from list.yaml"
                )
            if entry["percent"] != source.get("_percent"):
                reporter.error(
                    "metadata",
                    path,
                    f"{entry['name']} completeness differs from list.yaml",
                )
        # list.md is the complete human-readable rendering of list.yaml, not
        # merely a partial "recent additions" feed.
        for missing in sorted(set(by_name) - set(parsed[lang])):
            reporter.error(
                "metadata",
                path,
                f"list.yaml entry {by_name[missing].get('name')!r} is missing from list.md",
            )
    if "zh" in parsed and "en" in parsed:
        if set(parsed["zh"]) != set(parsed["en"]):
            reporter.error(
                "metadata",
                root / "docs" / "en" / "_meta" / "list.md",
                "Chinese and English list.md entries differ",
            )
        for key in set(parsed["zh"]) & set(parsed["en"]):
            if parsed["zh"][key] != parsed["en"][key]:
                reporter.error(
                    "metadata",
                    root / "docs" / "en" / "_meta" / "list.md",
                    f"list.md entry {parsed['zh'][key]['name']!r} differs between languages",
                )


def check_indexes(
    languages: dict[str, Path],
    actor_paths: dict[str, dict[str, Path]],
    reporter: Reporter,
) -> None:
    index_targets: dict[str, dict[str, set[str]]] = {}
    for lang, language_root in languages.items():
        actual = actor_paths[lang]
        directories = {PurePosixPath(filename).parts[0] for filename in actual}
        # Include the intentional empty Y directory when it is present.
        directories.update(
            path.name
            for path in language_root.iterdir()
            if path.is_dir()
            and len(path.name) == 1
            and path.name.isascii()
            and path.name.isalpha()
            and path.name.isupper()
        )
        targets_for_lang: dict[str, set[str]] = {}
        for directory in sorted(directories):
            index = language_root / directory / "index.md"
            if not index.exists():
                reporter.error("index", index, "letter directory is missing index.md")
                continue
            text = read_text(index, reporter)
            if text is None:
                continue
            if not HEADING_RE.search(text):
                reporter.error("empty", index, "index page has no Markdown heading")
            masked = mask_code(text)
            links, malformed = extract_inline_links(masked)
            for offset, message in malformed:
                reporter.error(
                    "links", index, f"{message} (line {line_number(masked, offset)})"
                )
            found: set[str] = set()
            for link in links:
                destination = link.destination
                if destination.startswith("#"):
                    continue
                try:
                    parsed = urlsplit(destination)
                except ValueError as exc:
                    reporter.error(
                        "links", index, f"malformed URL {destination!r}: {exc}"
                    )
                    continue
                if parsed.scheme:
                    continue
                target = (index.parent / unquote(parsed.path)).resolve()
                if target == index:
                    continue
                try:
                    relative = target.relative_to(language_root.resolve()).as_posix()
                except ValueError:
                    reporter.error(
                        "links",
                        index,
                        f"index link escapes language tree: {destination!r}",
                    )
                    continue
                if target.suffix.lower() == ".md" and target.parent.name == directory:
                    if relative in found:
                        reporter.error(
                            "index", index, f"duplicate actor link: {relative}"
                        )
                    found.add(relative)
                    label = re.sub(r"[`*_~]", "", link.label).strip()
                    expected_label = target.stem.replace("_", " ")
                    if label.casefold() != expected_label.casefold():
                        reporter.error(
                            "index",
                            index,
                            f"link label {link.label!r} does not match actor name {expected_label!r}",
                        )
                    check_destination(index, link, language_root, reporter)
            expected = {
                filename
                for filename in actual
                if PurePosixPath(filename).parts[0] == directory
            }
            if found != expected:
                for filename in sorted(expected - found):
                    reporter.error("index", index, f"missing actor link: {filename}")
                for filename in sorted(found - expected):
                    reporter.error("index", index, f"unexpected actor link: {filename}")
            targets_for_lang[directory] = found
        index_targets[lang] = targets_for_lang
    if "zh" in index_targets and "en" in index_targets:
        for directory in sorted(set(index_targets["zh"]) | set(index_targets["en"])):
            if index_targets["zh"].get(directory, set()) != index_targets["en"].get(
                directory, set()
            ):
                reporter.error(
                    "index",
                    languages["en"] / directory / "index.md",
                    "Chinese and English index link sets differ",
                )


def check_pages(
    languages: dict[str, Path],
    actor_paths: dict[str, dict[str, Path]],
    reporter: Reporter,
) -> dict[str, dict[str, Any]]:
    metadata_by_lang: dict[str, dict[str, Any]] = {"zh": {}, "en": {}}
    for lang, language_root in languages.items():
        for path in sorted(language_root.rglob("*.md")):
            text = read_text(path, reporter)
            if text is None:
                continue
            relative = path.relative_to(language_root).as_posix()
            if not (
                relative == "index.md"
                or relative.endswith("/index.md")
                or relative.startswith("_meta/")
                or is_actor_path(relative)
            ):
                reporter.error(
                    "paths",
                    path,
                    "Markdown page is outside the language/index/actor layout",
                )
            metadata, body = frontmatter_and_body(text, path, reporter)
            is_actor = is_actor_path(relative)
            if is_actor and metadata is None:
                reporter.error(
                    "frontmatter",
                    path,
                    "actor page must start with a YAML frontmatter block",
                )
            if metadata is not None:
                tags = metadata.get("tags")
                if is_actor and "tags" not in metadata:
                    reporter.error(
                        "frontmatter", path, "actor frontmatter must define tags"
                    )
                if tags is not None:
                    if not isinstance(tags, list):
                        reporter.error(
                            "frontmatter", path, "frontmatter.tags must be a list"
                        )
                    else:
                        if is_actor and not tags:
                            reporter.error(
                                "frontmatter",
                                path,
                                "actor frontmatter.tags must not be empty",
                            )
                        normalised_tags: list[str] = []
                        for tag in tags:
                            if not isinstance(tag, str) or not tag.strip():
                                reporter.error(
                                    "frontmatter",
                                    path,
                                    "every tag must be a non-empty string",
                                )
                                continue
                            clean_tag = tag.strip()
                            if not re.fullmatch(
                                r"[A-Za-z0-9][A-Za-z0-9 ._/+&-]*", clean_tag
                            ):
                                reporter.error(
                                    "security",
                                    path,
                                    f"tag contains characters outside the safe allowlist: {clean_tag!r}",
                                )
                            normalised_tags.append(clean_tag.casefold())
                        duplicates = sorted(
                            {
                                tag
                                for tag in normalised_tags
                                if normalised_tags.count(tag) > 1
                            }
                        )
                        if duplicates:
                            reporter.error(
                                "frontmatter",
                                path,
                                f"duplicate tags: {', '.join(duplicates)}",
                            )
                if is_actor:
                    metadata_by_lang[lang][relative] = metadata

            visible_body = re.sub(r"<!--.*?-->", "", mask_code(body), flags=re.DOTALL)
            if not any(char.isalnum() for char in visible_body):
                reporter.error("empty", path, "page has no non-whitespace content")

            if is_actor:
                markdown_body = mask_code(body)
                heading = markdown_heading(markdown_body)
                if not heading:
                    reporter.error(
                        "structure", path, "actor page must have exactly one H1"
                    )
                else:
                    expected_name = path.stem.replace("_", " ")
                    if heading.casefold() != expected_name.casefold():
                        reporter.error(
                            "structure",
                            path,
                            f"H1 {heading!r} does not match filename {expected_name!r}",
                        )
                h1_count = len(re.findall(r"^#\s+.+$", markdown_body, re.MULTILINE))
                if h1_count != 1:
                    reporter.error(
                        "structure",
                        path,
                        f"actor page must have exactly one H1 (found {h1_count})",
                    )

            links = check_markdown_links_and_security(
                path, body, language_root, reporter
            )
            check_handles(path, body, links, reporter)
    if "zh" in metadata_by_lang and "en" in metadata_by_lang:
        for relative in sorted(
            set(metadata_by_lang["zh"]) & set(metadata_by_lang["en"])
        ):
            zh_tags = metadata_by_lang["zh"][relative].get("tags")
            en_tags = metadata_by_lang["en"][relative].get("tags")
            if (
                isinstance(zh_tags, list)
                and isinstance(en_tags, list)
                and [str(tag).casefold() for tag in zh_tags]
                != [str(tag).casefold() for tag in en_tags]
            ):
                reporter.error(
                    "frontmatter",
                    languages["en"].joinpath(relative),
                    "tags differ between language versions",
                )
    return metadata_by_lang


def check_bilingual_handles(
    languages: dict[str, Path],
    actor_paths: dict[str, dict[str, Path]],
    reporter: Reporter,
) -> None:
    for relative in sorted(set(actor_paths["zh"]) & set(actor_paths["en"])):
        pairs: dict[str, set[tuple[str, str]]] = {}
        prose_handles: dict[str, set[str]] = {}
        for lang in LANGUAGES:
            text = read_text(actor_paths[lang][relative], reporter) or ""
            _, body = frontmatter_and_body(text, actor_paths[lang][relative], reporter)
            masked = mask_code(body)
            links, _ = extract_inline_links(masked)
            pairs[lang] = {
                pair
                for link in links
                if (pair := url_handle(link.destination)) is not None
            }
            prose_handles[lang] = {
                normalise_handle(value) for value in HANDLE_RE.findall(body)
            }
        if pairs["zh"] != pairs["en"]:
            reporter.error(
                "handles",
                languages["en"].joinpath(relative),
                "social URL handles differ between language versions",
            )
        if prose_handles["zh"] != prose_handles["en"]:
            reporter.error(
                "handles",
                languages["en"].joinpath(relative),
                "prose @handles differ between language versions",
            )


def check_paths(root: Path, languages: dict[str, Path], reporter: Reporter) -> None:
    if set(languages) != set(LANGUAGES):
        return
    zh_files = relative_files(languages["zh"])
    en_files = relative_files(languages["en"])
    for filename in sorted(zh_files - en_files):
        reporter.error(
            "i18n", languages["en"] / filename, "path is missing from the English tree"
        )
    for filename in sorted(en_files - zh_files):
        reporter.error(
            "i18n", languages["zh"] / filename, "path is missing from the Chinese tree"
        )
    for filename in sorted(zh_files & en_files):
        if "\\" in filename or ".." in PurePosixPath(filename).parts:
            reporter.error(
                "i18n", root / "docs" / filename, "non-canonical relative path"
            )
    for language_root in languages.values():
        for child in language_root.iterdir():
            if child.name == "_meta":
                continue
            if child.is_dir() and not (
                len(child.name) == 1
                and child.name.isascii()
                and child.name.isalpha()
                and child.name.isupper()
            ):
                reporter.error(
                    "paths",
                    child,
                    "language tree contains a directory outside the uppercase-letter layout",
                )
        for path in language_root.rglob("*"):
            if path.is_symlink():
                reporter.error(
                    "paths", path, "symlinks are not allowed in documentation trees"
                )
            elif path.is_file():
                relative = path.relative_to(language_root).as_posix()
                if not relative.startswith("_meta/") and path.suffix.lower() != ".md":
                    reporter.error(
                        "paths",
                        path,
                        "only Markdown files are allowed outside docs/_meta",
                    )


def validate(root: Path) -> Reporter:
    reporter = Reporter(root)
    languages = {lang: root / "docs" / lang for lang in LANGUAGES}
    for language_root in languages.values():
        if not language_root.is_dir():
            reporter.error(
                "paths", language_root, "language documentation directory is missing"
            )
    if any(not language_root.is_dir() for language_root in languages.values()):
        return reporter

    check_paths(root, languages, reporter)
    check_config_contracts(root, reporter)
    actor_paths = {
        lang: actor_files(language_root) for lang, language_root in languages.items()
    }
    for paths in actor_paths.values():
        for relative, path in paths.items():
            pure = PurePosixPath(relative)
            if (
                len(pure.parts[0]) != 1
                or not pure.parts[0].isascii()
                or not pure.parts[0].isalpha()
                or not pure.parts[0].isupper()
            ):
                reporter.error(
                    "structure",
                    path,
                    "actor path must use a one-letter uppercase directory",
                )
            if not is_actor_path(relative):
                reporter.error("structure", path, "unexpected actor page path")
    lists, _ = check_lists(root, languages, reporter)
    check_list_md(root, languages, lists, reporter)
    check_indexes(languages, actor_paths, reporter)
    check_pages(languages, actor_paths, reporter)
    check_bilingual_measurements(actor_paths, reporter)
    check_bilingual_handles(languages, actor_paths, reporter)
    return reporter


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of this script)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.expanduser().resolve()
    reporter = validate(root)
    if reporter.errors:
        reporter.emit()
        return 1
    count = len(actor_files(root / "docs" / "zh"))
    print(
        f"documentation validation passed ({count} actor pages; i18n trees match and build contracts are consistent)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
