# Adult Film Performer Encyclopedia

**English** | [简体中文](README.zh-CN.md)

This repository uses Zensical to build a bilingual Chinese-English encyclopedia, with English as the default language. Chinese content lives in `docs/zh/`, English content in `docs/en/`, and matching pages use the same relative path.

See [TRANSLATION.md](TRANSLATION.md) (in Chinese) for the translation models, measured performance, quality limitations, and maintenance workflow.

> **English status:** `docs/en/` currently contains machine-translated drafts. The articles have not yet been individually researched again, rewritten, or subjected to a consistent human fact-checking process. A successful strict build only confirms that file structure and site builds pass; it does not verify English content, names, numbers, awards, or sources.

## Directory and `index.md` conventions

- `docs/zh/<letter>/<stage_name>.md` and `docs/en/<letter>/<stage_name>.md` are paired Chinese and English articles and must have identical relative paths.
- `docs/zh/<letter>/index.md` and `docs/en/<letter>/index.md` are maintained alphabetical directory indexes, not `README.md` files. The root README files document the project; do not create README files as indexes inside content directories.
- When adding, deleting, or renaming an article, update the corresponding `index.md` in both languages. Link targets must match article filenames, and entries are generally sorted by name. Update performer counts or summaries if the index includes them.
- Each new letter directory needs an `index.md` in both languages, following the existing simple or full format used by that directory.
- Older documentation described `docs/{zh,en}/_meta/award/index.md` as a CI-generated page. The current build script and CI do not generate it. Award directories and old placeholder files are not factual sources for new articles; do not rely on, create, or manually edit them as a substitute for source verification.
- `overrides/` contains shared templates for the bilingual 404 page and page-level language links. Article maintenance generally does not require changes to these files.

## Local prerequisites

Run maintenance commands from the repository root. You need:

- Git;
- Python 3.12.x (`python3.12 --version`; `pyproject.toml` requires `>=3.12,<3.13`);
- `uv` 0.12.5–0.12.x (`uv --version`; `pyproject.toml` requires `>=0.12.5,<0.13`).

Install or refresh the locked environment:

```bash
uv sync --locked
```

`pyproject.toml` pins the direct dependencies to `pyyaml==6.0.2` and `zensical==0.0.62`, and the development dependency to `ruff==0.16.8`. `uv.lock` locks resolved transitive dependencies and hashes. Zensical itself supports Python 3.10 and later, but this project uses Python 3.12 to keep the lockfile and local/CI environments consistent. Do not edit `uv.lock` manually; update it through `uv` after dependency changes and review the result.

## Preview, build, and full validation

Run all commands below from the repository root. If your shell is inside the repository but outside its root, locate the root using your current directory:

```bash
cd "$(git -C . rev-parse --show-toplevel)"
```

`./scripts/build_site.sh` also derives the root from its own location. The explicit `uv run --project .` commands below still assume the repository root is the current directory.

### Preview

Use the environment locked by `uv.lock`, rather than an unlocked global `zensical` installation:

```bash
# English (default language, site root)
uv run --locked --project . zensical serve --config-file zensical.toml

# Chinese
uv run --locked --project . zensical serve --config-file zensical.zh.toml
```

### Full validation

Run the repository's full validation script before every push, including documentation and workflow changes. Rerun it after any further edits; push only when it succeeds:

```bash
./scripts/build_site.sh
```

The script derives the repository root from its own location and runs the following steps in the locked `uv` environment:

1. Check the Python validators with the locked Ruff linter and formatter.
2. Run `check_i18n.py` to check bilingual file sets and canonical paths, the Zensical configuration contract, article front matter/tags/H1 headings, `list.yaml`/`list.md`, alphabetical `index.md` links, local Markdown targets, and security/Markdown issues such as unsafe HTML or protocols. It also compares social handles and recognizable heights, weights, work counts, percentages, and quantities expressed with `万` (ten thousand) or `亿` (one hundred million). This script does not access the network.
3. Build the English site, then the Chinese site, with locked Zensical 0.0.62 and `--clean --strict` in a temporary staging directory inside the repository. Chinese output is nested under `site/zh/`. If either build fails, the previous `site/` is preserved.
4. Verify both entry points, both 404 pages, redirects for Elle Lee's old paths, and redirects for retired `/corn/en/*` paths before replacing the final `site/` on the same filesystem.
5. Copy the root `LICENSE` and `NOTICE` into the published output.

For individual diagnostics, run:

```bash
uv run --locked --project . ruff check scripts
uv run --locked --project . ruff format --check scripts
uv run --locked --project . python scripts/check_i18n.py --root .
uv run --locked --project . zensical build --config-file zensical.toml --clean --strict
uv run --locked --project . zensical build --config-file zensical.zh.toml --clean --strict
```

Also run `git diff --check` before pushing to check whitespace errors; it does not replace the full site validation. Inspect `git status` and stage only intended files before committing and pushing to `main`.

### GitHub Actions deployment

[`.github/workflows/docs.yml`](.github/workflows/docs.yml) follows the [official Zensical GitHub Pages workflow](https://zensical.org/docs/publish-your-site/#with-github-actions), using GitHub’s `configure-pages`, `checkout`, `setup-python`, `upload-pages-artifact`, and `deploy-pages` actions. The project retains Python 3.12.11, `uv==0.12.5`, locked dependencies, and `./scripts/build_site.sh` to validate and build both languages before uploading `site/`.

Pull requests run validation without deployment permissions. Pushes to `main` and manual runs on `main` build and deploy through the `github-pages` environment. CI checks run after a push and do not replace the required local checks before pushing. In repository **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions**; changing this setting requires repository administration access.

English is the default language, occupies the site root, and is published at `/corn/`; Chinese is published at `/corn/zh/`. `site/` and `site/zh/` are build outputs ignored by `.gitignore`; do not commit them. English was previously published at `/corn/en/`, and every previously published page under that prefix retains a redirect to its new root-level path. The validator prevents missing redirects. Previously published Chinese URLs under `/corn/` now display the same performer's English page.

The header language selector and page-level `hreflang` links preserve the current performer path. The root 404 page is bilingual so that an invalid language-specific path does not show only the other language. The theme uses system fonts and makes no requests to Google Fonts. Published output includes `LICENSE` and `NOTICE`.

If you fork the repository, rename it, migrate domains, or change the default branch, update the `site_url`, alternate-language, and repository paths in both Zensical configurations, along with the default-language, canonical-URL, and directory constants in `scripts/check_i18n.py`. Shared templates read language homepages from the configuration; the validator intentionally blocks deployments whose settings have not been updated together.

The validator's checks for numbers, units, handles, and links only establish bilingual structure and consistency. They do not check whether external URLs are accessible, whether sources support a fact, whether English translations are correct, or whether award information is outdated. These still require human review.

## Content, sensitive information, and source rules

- Base performer profiles on publicly accessible, verifiable sources wherever possible. Prefer the person's own or official accounts, official or award-organization pages, reliable interviews, and databases. Keep original links, source names, and verification dates or scope in the article.
- Dates of birth, real/legal names, gender identity, sexual orientation, health, family relationships, addresses, contact details, and other identifying personal information are sensitive. Include only what is necessary for the public interest, actually public, and supported by reliable sources. Do not infer information from stage names, photos, tags, or third-party speculation, or aggregate information that could enable harassment or locate someone. If unconfirmed, write “not disclosed” or “unconfirmed,” or omit it and reduce the information-completeness rating.
- Changing data, such as work counts, activity status, platform accounts, and follower counts, must include a source and verification date, with the counting scope explained (for example, IAFD records as of a specified date). IAFD profile links use `https://www.iafd.com/person.rme/id=<UUID>`; the UUID must come from an actual source page and must not be guessed. Do not present outdated numbers as current facts without a date qualifier.
- Distinguish award wins from nominations. Record the year, award/organization, category, and result, and verify them against currently accessible public sources. Award tags do not replace sources, and old award placeholder files must not be used to infer results.
- Do not invent people, works, sources, accounts, numbers, or URLs. If sources conflict, retain their attribution and clearly mark the conflict as unresolved; do not choose whichever claim best matches a guess.
- Preserve Markdown link targets, relative paths, proper nouns, and account handles verbatim. Local links should point to existing targets. Avoid unauthorized raw HTML, unsafe protocols, and unescaped Markdown mathematical symbols. After any translation or edit, check that these remain consistent with the sources.

## English edition and human review

The English edition currently consists of machine-translated drafts. Before committing any new article or change:

1. Identify the Chinese source file and matching path.
2. Check structure and protected strings (numbers, dates, URLs, handles, IDs, and code).
3. Have a human review English proper nouns, headings, terminology, grammar, pronouns, and gender/identity wording.
4. Have a human return to public sources to verify facts, sensitive information, source titles, awards, and changing data.
5. Synchronize articles, alphabetical `index.md` files, and related metadata in both languages.
6. Run the full strict build again.

See [TRANSLATION.md](TRANSLATION.md) (in Chinese) for the detailed record of the current English status and maintenance limitations. Until these reviews are complete, neither a successful English build nor machine-translated output should be described as “verified.”
