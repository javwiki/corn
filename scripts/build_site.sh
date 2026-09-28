#!/usr/bin/env sh
set -eu

# Resolve the repository from the script location instead of the caller's cwd.
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
ROOT_DIR=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$ROOT_DIR"

STAGE_PARENT=$(mktemp -d "$ROOT_DIR/.site-stage.XXXXXX")
STAGE_DIR="$STAGE_PARENT/build"
EN_CONFIG="$ROOT_DIR/.zensical-stage.$$.en.toml"
ZH_CONFIG="$ROOT_DIR/.zensical-stage.$$.zh.toml"
OLD_PARENT=""
OLD_SITE=""

cleanup() {
    status=$?
    rm -f "$EN_CONFIG" "$ZH_CONFIG"
    rm -rf "$STAGE_PARENT"
    if [ -n "$OLD_SITE" ] && [ -d "$OLD_SITE" ] && [ ! -e "$ROOT_DIR/site" ]; then
        mv "$OLD_SITE" "$ROOT_DIR/site"
    fi
    if [ -n "$OLD_PARENT" ] && [ -d "$OLD_PARENT" ]; then
        rmdir "$OLD_PARENT" 2>/dev/null || rm -rf "$OLD_PARENT"
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# Validate before creating or replacing a deliverable. A non-zero validation
# result leaves any previous site/ output untouched.
uv run --locked --project "$ROOT_DIR/pyproject.toml" ruff check "$SCRIPT_DIR"
uv run --locked --project "$ROOT_DIR/pyproject.toml" ruff format --check "$SCRIPT_DIR"
uv run --locked --project "$ROOT_DIR/pyproject.toml" python "$SCRIPT_DIR/check_i18n.py" --root "$ROOT_DIR"

mkdir -p "$STAGE_DIR"

# Build both languages into a staging tree.  The tracked configs remain the
# source of truth, while root-level temporary copies only override site_dir.
# Keeping the temporary configs beside the tracked files preserves Zensical's
# requirement that docs_dir remain inside the project root.  English is the
# default language and therefore owns the site root; Chinese is nested below it.
sed \
    -e "s|^site_dir = .*|site_dir = \"$STAGE_DIR/site\"|" \
    "$ROOT_DIR/zensical.toml" > "$EN_CONFIG"
sed \
    -e "s|^site_dir = .*|site_dir = \"$STAGE_DIR/site/zh\"|" \
    "$ROOT_DIR/zensical.zh.toml" > "$ZH_CONFIG"

uv run --locked --project "$ROOT_DIR/pyproject.toml" zensical build \
    --config-file "$EN_CONFIG" \
    --clean \
    --strict
uv run --locked --project "$ROOT_DIR/pyproject.toml" zensical build \
    --config-file "$ZH_CONFIG" \
    --clean \
    --strict

# Verify the staged deliverable before replacing the previous one.
test -f "$STAGE_DIR/site/index.html"
test -f "$STAGE_DIR/site/zh/index.html"
test -f "$STAGE_DIR/site/404.html"
test -f "$STAGE_DIR/site/zh/404.html"
test -f "$STAGE_DIR/site/L/Elle_Lee/index.html"
test -f "$STAGE_DIR/site/zh/L/Elle_Lee/index.html"
grep -Fq '../../E/Elle_Lee/' "$STAGE_DIR/site/L/Elle_Lee/index.html"
grep -Fq '../../E/Elle_Lee/' "$STAGE_DIR/site/zh/L/Elle_Lee/index.html"
# The English edition moved from /corn/en/ to the site root; the retired paths
# must keep redirecting instead of returning 404.
test -f "$STAGE_DIR/site/en/index.html"
test -f "$STAGE_DIR/site/en/A/Angela_White/index.html"
grep -Fq 'url=../"' "$STAGE_DIR/site/en/index.html"
grep -Fq 'url=../../../A/Angela_White/"' "$STAGE_DIR/site/en/A/Angela_White/index.html"
cp "$ROOT_DIR/LICENSE" "$STAGE_DIR/site/LICENSE"
cp "$ROOT_DIR/NOTICE" "$STAGE_DIR/site/NOTICE"

# Swap directories on the same filesystem. If the second rename fails, the EXIT
# trap restores the previous site/ output.
if [ -d "$ROOT_DIR/site" ] || [ -L "$ROOT_DIR/site" ]; then
    OLD_PARENT=$(mktemp -d "$ROOT_DIR/.site-previous.XXXXXX")
    OLD_SITE="$OLD_PARENT/site"
    mv "$ROOT_DIR/site" "$OLD_SITE"
fi
mv "$STAGE_DIR/site" "$ROOT_DIR/site"
if [ -n "$OLD_PARENT" ]; then
    rm -rf "$OLD_PARENT"
fi
OLD_PARENT=""
OLD_SITE=""
