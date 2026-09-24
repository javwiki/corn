# 成人影片演员百科 / Adult Film Performer Encyclopedia

本仓库使用 Zensical 构建中英双语人物资料型百科。中文内容位于 `docs/zh/`，英文内容位于 `docs/en/`；两个目录使用相同的相对路径。

This repository uses Zensical to build a bilingual Chinese-English encyclopedia. Chinese content lives in `docs/zh/`, English content in `docs/en/`, and matching pages use the same relative path.

翻译所用模型、实测速度、质量限制与维护流程见 [TRANSLATION.md](TRANSLATION.md)。

> **英文版状态 / English status:** `docs/en/` 当前是机器翻译初稿，尚未逐篇重新调查、重新编写或完成统一的人工事实复核。严格构建成功只说明文件结构和站点构建通过，不表示英文内容、人名、数字、奖项或来源已经核实。

## 目录与 `index.md` 约定

- `docs/zh/<字母>/<艺名>.md` 与 `docs/en/<字母>/<艺名>.md` 是成对的中英文条目，必须保持相同的相对路径。
- `docs/zh/<字母>/index.md` 与 `docs/en/<字母>/index.md` 是需要维护的字母目录索引，不是 `README.md`。根目录的 `README.md` 只用于说明项目，内容目录中不要另建 README 作为索引。
- 新增、删除或改名人物条目时，同步更新两种语言的对应 `index.md`；链接目标必须与条目文件名一致，通常按姓名排序。如果索引已有演员数量或概要，也要同步更新。
- 新字母目录需要在两种语言中各有一个 `index.md`，并沿用该目录现有的简单或完整格式。
- 旧版说明曾把 `docs/{zh,en}/_meta/award/index.md` 描述为 CI 生成页面；当前构建脚本和 CI 没有生成该页面的步骤。award 目录或旧占位文件不是新增人物条目的事实来源；不要依赖、创建或手改它们来代替来源核验。
- `overrides/` 保存中英文共享的 404 和页面级语言链接模板；人物条目维护通常不需要修改这些文件。

## 本地前置条件

在仓库根目录执行维护命令。需要：

- Git；
- Python 3.12.x（`python3.12 --version`；`pyproject.toml` 要求 `>=3.12,<3.13`）；
- `uv` 0.12.5–0.12.x（`uv --version`；`pyproject.toml` 要求 `>=0.12.5,<0.13`）。

首次安装或刷新锁定环境：

```bash
uv sync --locked
```

`pyproject.toml` 固定直接依赖 `pyyaml==6.0.2`、`zensical==0.0.62`，开发依赖固定为 `ruff==0.16.8`；`uv.lock` 锁定解析后的传递依赖与哈希。Zensical 本身最低支持 Python 3.10，但本项目选择 Python 3.12 以保持锁文件与本地/CI 环境一致。不要手改 `uv.lock`；依赖变更后应通过 `uv` 更新并审阅锁文件。

## 预览、构建与完整校验

以下命令都应从仓库根目录执行。如果当前 shell 位于仓库内但不在根目录，可先用当前目录定位仓库根目录：

```bash
cd "$(git -C . rev-parse --show-toplevel)"
```

`./scripts/build_site.sh` 自身也会从脚本位置推导根目录；下面显式的 `uv run --project .` 命令仍以仓库根目录为当前目录。

### 预览

预览时使用 `uv.lock` 锁定的环境，不使用未锁定的全局 `zensical`：

```bash
# 中文
uv run --locked --project . zensical serve --config-file zensical.toml

# 英文
uv run --locked --project . zensical serve --config-file zensical.en.toml
```

### 完整校验

提交前运行仓库提供的完整校验脚本：

```bash
./scripts/build_site.sh
```

该脚本会从自身位置推导仓库根目录，并在锁定的 `uv` 环境中依次执行：

1. 使用锁定的 Ruff 检查 Python 校验器的 lint 和格式；
2. `check_i18n.py`：检查双语文件集合与规范路径、Zensical 配置契约、条目 front matter/tags/H1、`list.yaml`/`list.md`、字母 `index.md` 链接、本地 Markdown 目标，以及危险 HTML/协议等安全和 Markdown 问题；同时比较双语社交 handle，以及可识别的身高、体重、作品数量、百分比和 `万/亿` 数量级。该脚本不访问网络；
3. 在仓库内临时 staging 目录中，用锁定的 Zensical 0.0.62 以 `--clean --strict` 分别构建中文和英文站点；任一构建失败时保留上一份 `site/`；
4. 验证两个入口、两个 404 页面和 Elle Lee 旧路径重定向后，才在同一文件系统内替换正式 `site/`；
5. 将根目录的 `LICENSE` 与 `NOTICE` 复制进发布产物。

需要单独诊断时可以运行：

```bash
uv run --locked --project . ruff check scripts
uv run --locked --project . ruff format --check scripts
uv run --locked --project . python scripts/check_i18n.py --root .
uv run --locked --project . zensical build --config-file zensical.toml --clean --strict
uv run --locked --project . zensical build --config-file zensical.en.toml --clean --strict
```

提交前还可以运行 `git diff --check` 检查空白错误；它不是站点构建校验。

`site/` 和 `site/en/` 是构建产物，已被 `.gitignore` 忽略，不要提交。现有中文版 URL 保持不变，英文版发布在 `/en/`；页眉语言选择器和页面级 `hreflang` 会保留当前人物路径。根 404 页面为双语，避免英文路径错误时只显示中文；主题使用系统字体，不向 Google Fonts 发起请求。发布产物包含 `LICENSE` 与 `NOTICE`。如果 fork、改名、迁移域名或更改默认分支，必须同步修改两份 Zensical 配置中的 `site_url`/alternate/repository 路径，以及 `scripts/check_i18n.py` 中的 canonical URL/目录常量；共享模板会从配置读取语言首页，校验器会故意阻止未同步的部署。校验器对数字、单位、handle 和链接的检查只说明双语结果的结构/一致性，不检查外部 URL 是否可访问、来源是否支持某项事实、英文翻译是否正确或奖项信息是否过时；这些仍需要人工复核。

## 内容、敏感信息与来源规则

- 人物资料应尽量依据可公开访问、可复核的来源。优先使用本人/官方账号、官方或 award 机构页面、可靠采访和数据库，并在条目中保留原始链接、来源名称以及核验日期或核验口径。
- 出生日期、本名/法定姓名、性别认同、性取向、健康、家庭关系、地址、联系方式和其他可识别个人的信息属于敏感信息。只写完成公共利益所必需、确实公开且有可靠来源支持的内容；不要从艺名、照片、标签或第三方猜测，也不要汇总可用于骚扰或定位个人的信息。无法确认时写“未公开”“未确认”或不写，并降低信息完整度。
- 作品数量、活跃状态、平台账号、粉丝数等会变化的数据必须注明来源和核验日期，并说明统计口径（例如 IAFD 记录截至某日）。IAFD 人物链接使用 `https://www.iafd.com/person.rme/id=<UUID>` 格式，UUID 必须来自实际来源页面，不能猜测。不要把过时数字写成无时间限定的当前事实。
- 奖项信息要区分获奖与提名，记录年份、奖项/机构、类别和结果，并使用当前可访问的公开来源核对。奖项标签不能替代来源，也不能从旧的 award 占位文件推断。
- 不要编造人物、作品、来源、账号、数字或 URL；来源冲突时要保留出处并明确标注未解决，不要擅自选择最符合猜测的说法。
- 保留 Markdown 链接目标、相对路径、专有名词和账号 handle 的原样；本地链接应指向存在的目标，避免未授权的 raw HTML、危险协议和未转义的 Markdown 数学符号。任何翻译或编辑后都要检查它们是否仍与来源一致。

## 英文版与人工复核

英文版目前是机器翻译草稿。任何新条目或修改在提交前都应：

1. 先确定中文源文件和对应路径；
2. 做结构与受保护字符串（数字、日期、URL、handle、ID、代码）检查；
3. 由人工检查英文专有名词、标题、术语、语法、代词和性别/身份表述；
4. 由人工回到公开来源复核事实、敏感信息、来源标题、奖项和会变化的数据；
5. 同步两种语言的条目、字母 `index.md` 及相关元数据；
6. 再运行完整 strict 构建。

本次英文状态和维护限制的详细记录见 [TRANSLATION.md](TRANSLATION.md)。在这些复核完成前，不应把英文构建成功或机器翻译结果描述为“已核实”。
