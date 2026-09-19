#!/usr/bin/env sh
set -eu

python3 scripts/check_i18n.py
uvx --from zensical==0.0.62 zensical build --config-file zensical.toml --clean --strict
uvx --from zensical==0.0.62 zensical build --config-file zensical.en.toml --clean --strict
