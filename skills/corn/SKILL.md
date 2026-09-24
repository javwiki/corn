---
name: corn-add-entry
description: "在当前 corn 仓库新增成人影片演员条目。当用户要求添加演员/新人、收录某位表演者或新增双语条目时使用。覆盖公开来源核验、创建 docs/zh 与 docs/en 条目、同步字母目录 index.md 和相关元数据，并提醒英文机器翻译初稿需要人工复核。不负责删除条目。"
metadata:
  requires:
    bins: ["git", "python3", "uv"]
---

# 添加条目（corn 百科）

## 先定位仓库并检查状态

**CRITICAL — 动手前 MUST 先定位当前 checkout，保留已有用户改动，并检查最近提交风格。不要假定仓库位于任何固定绝对路径。**

如果当前 shell 已在仓库内，使用当前目录推导仓库根目录：

```bash
REPO_ROOT="$(git -C . rev-parse --show-toplevel)"
cd "$REPO_ROOT"
git -C . status --short
git -C . log --oneline -5
```

如果当前目录不在仓库内，先使用实际读取到的 `skills/corn/SKILL.md` 所在目录：从该 skill 目录向上两级得到仓库候选目录，再用 `git -C <候选目录> rev-parse --show-toplevel` 验证并 `cd` 到输出目录。不要把示例中的占位符当作真实路径，也不要使用任何机器专用的固定绝对路径。

## 适用场景

- “给百科添加 XX”
- “新增演员 XX 的条目”
- “把 XX 收录进去” / “XX 能加进百科吗”
- 用户给出演员名（常见于 AVN 获奖者、trans 表演者、IAFD 有记录者）

## 项目结构

新增或修改条目通常涉及以下源文件；所有路径都相对于推导出的仓库根目录：

```text
docs/zh/<字母>/<艺名>.md       ← 中文条目文件
docs/en/<字母>/<艺名>.md       ← 英文条目文件（与中文保持相同相对路径）
docs/zh/<字母>/index.md        ← 中文字母目录索引，需同步
docs/en/<字母>/index.md        ← 英文字母目录索引，需同步
docs/{zh,en}/_meta/list.yaml   ← 条目数据源（含 completeness）
docs/{zh,en}/_meta/list.md     ← 当前 checked-in 的人类可读列表；按仓库现状处理
docs/{zh,en}/_meta/source.yaml ← 来源登记表；只登记实际使用的公开来源
scripts/check_i18n.py          ← 双语文档结构/安全/一致性校验
scripts/build_site.sh          ← 锁定环境中的完整双语构建
pyproject.toml                 ← Python/直接依赖与 uv 版本约束
uv.lock                        ← 锁定的传递依赖与哈希
zensical.toml                  ← 中文 Zensical 配置
zensical.en.toml               ← 英文 Zensical 配置
overrides/                     ← 双语 404 与页面级语言链接共享模板
```

`docs/{zh,en}/<字母>/index.md` 是内容索引，不是 README。根目录 `README.md` 是项目维护说明；不要在内容字母目录中创建 `README.md` 来代替 `index.md`。

旧版说明曾把 `docs/{zh,en}/_meta/award/index.md` 描述为 CI 生成页面；当前构建脚本和 CI 没有生成该页面的步骤。award 目录或旧占位文件不是新增人物条目的事实来源；不要依赖、创建或手改它们，奖项事实应直接依据可核验的公开来源写入条目（如确有必要）。

## 工作流

```text
演员名 ─┬─► 信息核验（公开来源；IAFD 格式按规范）──► 确定字母与文件名
        │
        ├─► 创建 docs/zh/<字母>/<艺名>.md（front matter + 概要 + 详情 + 参考资料）
        ├─► 创建对应 docs/en/<字母>/<艺名>.md，并同步两种语言的 index.md
        ├─► 更新 docs/{zh,en}/_meta/list.yaml（按实际证据填写 completeness）
        ├─► 同步 list.md（当前没有自动生成器；不要声称由 CI 生成）
        └─► 文件检查 + 英文人工复核 + ./scripts/build_site.sh
```

### Step 1: 信息核验（先查证，再动笔）

- 以公开、可复核的来源为准。IAFD 可用于作品记录和数据库统计，Wikipedia/Wikidata、官方或本人账号、可靠采访和行业/奖项机构可互相交叉核对；任何单一数据库都不是所有身份事实的绝对权威。
- IAFD 人物链接使用如下格式（把 UUID 替换为从实际 IAFD 页面复制的值）：

  ```text
  https://www.iafd.com/person.rme/id=<IAFD_PERSON_UUID>
  ```

  不要使用 `person.rme` 的 query-string 形式，不要猜 UUID，也不要凭姓名拼造链接。实际来源链接若带有 `/gender=f` 等可选路径后缀，只在确认后原样保留。
- 作品数量、活跃状态、粉丝数等动态数据注明来源和核验日期/口径，例如“IAFD 记录截至 YYYY-MM-DD”；不要把数据库数字写成无时间限定的当前事实。
- 奖项要区分获奖与提名，并核对年份、机构、类别和结果。不要从旧的 award 占位文件、标签或未经核实的二手摘要推断奖项。
- 信息不足时如实标注，**不要编造**（如“别名：无记录”“出生：未公开”“活跃年代：未知”）。无法确认时宁可降低 completeness，也不补写猜测。
- 本名/法定姓名、出生日期、出生地、性取向、性别认同、健康、家庭关系、地址、联系方式等敏感信息，只写公共利益所必需且有可靠公开来源支持的内容；不要从艺名、照片、标签或第三方推断，也不要汇总可用于骚扰或定位个人的信息。

### Step 2: 确定字母目录与文件名

- 按**艺名首字母**分目录：`Sky Bri` → `docs/zh/S/Sky_Bri.md` 和 `docs/en/S/Sky_Bri.md`；`Bridgette B` → `docs/zh/B/Bridgette_B.md` 和 `docs/en/B/Bridgette_B.md`。
- 文件名沿用仓库约定：艺名中的空格以 `_` 连接，不随意加入其他特殊符号；若对应字母目录不存在，在两种语言中同时新建。
- 跨性别演员按已确认的当前艺名首字母归档，不按未经核实的本名归档；不要为满足模板而猜测身份信息。
- 不要为了本次新增而重命名已有条目，除非用户明确要求并同步处理所有双语路径和索引。

### Step 3: 创建条目文件

按下面模板写，字段可按实际情况增删；完整条目可以增加身高、体重、三围、发色等，但每项都要有来源支持：

```markdown
---
tags:
  - pornstar
  - Adult Actress
  - <国籍，如 American / Australian / Japanese / South Korean>
  - <身材/发色，如 Big Tits / petite / blonde>
  - <主要制片公司，如 Brazzers / Blacked / Grooby>
  - <平台，如 OnlyFans / ManyVids>
  - <奖项/荣誉，如 AVN / XBIZ；只有来源确认时才添加>
  # 跨性别演员标签：只有公开资料支持时添加
  # - transgender
---

# <艺名>

## 概要

- **名称**: <艺名>
- **别名**: <别名，无则写“无记录”>
- **平台**: OnlyFans / Twitter / Instagram（有哪个写哪个，无则写“未指定”）
- **出生**: YYYY年M月D日，<国家>（信息不可靠则写“未公开”）
- **活跃年代**: YYYY – 至今（或 YYYY – YYYY）
- **作品数量**: N 部（来源：IAFD / 其他已核验来源，注明口径和日期）
- **职业**: <成人影片演员、模特、导演、内容创作者等；按实际填写>
- **备注**: <一两句有来源的亮点：签约公司、奖项、成名作>

## 详情

<3–5 段生平与职业生涯，附可核验来源；不要为了填满模板而添加未经证实的生活细节。涉奖项时可加子表。>

### 奖项与提名

| 年份 | 奖项/机构 | 类别 | 结果 |
|---|---|---|---|
| YYYY | <官方奖项名称> | <官方类别> | 获奖/提名/未确认 |

## 参考资料

- [<艺名> - Wikipedia](https://en.wikipedia.org/wiki/...)
- [<艺名> - IAFD](https://www.iafd.com/person.rme/id=...)
- [X/Twitter: @handle](https://x.com/handle)
- [Instagram: @handle](https://www.instagram.com/handle/)
- [OnlyFans](https://onlyfans.com/...)
```

模板中的 `...`、`<...>` 和 `@handle` 都必须替换为实际值或删除；不能把占位符提交为来源。

**tags 规范**（对齐现有条目风格）：

- `pornstar`、`Adult Actress` 按现有项目约定添加；国籍、发色/身材、制片公司、平台、奖项/荣誉按实际证据添加。
- 不要添加具体作品/片名或场景标签，不要自造与现有风格不符的大小写（可参考 `Big Tits`、`blonde`、`webcam-model`、`content-creator`、`cosplayer`）。
- `transgender` 等身份标签不能仅由译名或推测得出；只在有可靠公开资料且符合项目编辑约定时使用。
- 敏感信息只写可核验来源支持的部分，并在正文或参考资料中给出处。

**内容约定**（与根目录 `README.md` 一致）：

- 资料附可核验的公开来源链接；来源不支持的内容不写。
- 会随时间变化的数据注明核验日期和统计口径。
- 不新增中文源和公开来源未支持的事实；来源冲突时标明冲突或未确认。

### Step 4: 更新字母目录 `docs/{zh,en}/<字母>/index.md`

- 这些是源文件中的 `index.md`，不是 README。若目录是简单格式（标题 + 链接列表），把新链接按姓名排序插入，例如 `- [<艺名>](<艺名>.md)`。
- 若目录是完整格式（含 `## 概要`、演员数量等字段，例如 `A/index.md`），同步更新数量/概要并插入列表。
- 中英文索引中的链接目标必须分别指向相同语种的同相对路径条目；新增或删除条目时两边都要更新。
- 新建字母目录时在 `docs/zh/` 与 `docs/en/` 各创建一个 `index.md`，沿用该目录现有的简单格式；不要创建 `README.md` 作为索引。
- 不要整体重排或改写无关索引；保留现有格式并在提交前检查链接目标存在。

### Step 5: 更新 `docs/{zh,en}/_meta/list.yaml`

- 在对应字母分组内按现有数据结构插入条目；不要为了新增一项重排整个 YAML。
- 至少保持以下字段与实际路径一致：

  ```yaml
  - completeness: <评分>
    name: <艺名>
    file: <X>/<艺名>.md
    index: <X>
  ```

- `completeness` 反映资料完整度，不是事实可信度的证明。可沿用以下起始标准，再根据证据调整：
  - 100%：概要字段齐全、详情充分且有多个可靠来源；
  - 90–95%：概要齐全，但详情或参考资料略有缺口；
  - 70–85%：出生、作品数、活跃状态等字段有明显缺口，或来源单一。
- 不要为了排名或视觉效果虚高填写；无法核验时应降低评分。
- 中英文 `list.yaml` 的条目集合和路径应保持对应。
- 如果本次新增了可复用的来源类别，再同步 `docs/{zh,en}/_meta/source.yaml`；不要为了填表登记未实际使用的网站。

### Step 6: 处理 `docs/{zh,en}/_meta/list.md`

- 该文件目前是仓库中 checked-in 的人类可读列表；`docs/{zh,en}/_meta/index.md` 将其标为自动生成，但当前 `scripts/` 和 CI 中没有对应生成器。
- 当前校验器会读取 `list.md` 并与 `list.yaml` 及另一语言列表交叉检查。新增、删除或改名人物时，应在中英文两份文件中按现有格式镜像变更并人工检查 diff；不要声称这些变更由当前 CI 自动生成。
- 不要把 `list.md` 当作事实来源，也不要让它取代条目本身和公开来源。

### Step 7: 校验、英文复核与交付

本地依赖是 Git、Python 3.12.x 和 `uv` 0.12.5–0.12.x。`pyproject.toml` 约束 Python/uv 版本并固定 `pyyaml==6.0.2`、`zensical==0.0.62`，开发依赖固定为 `ruff==0.16.8`；`uv.lock` 锁定传递依赖和哈希。首次安装或刷新环境使用 `uv sync --locked`，不要用未锁定的全局 `zensical` 替代；依赖变更后不要手改 lock 文件。

先做双语文档校验，再做完整构建：

```bash
uv run --locked --project . ruff check scripts
uv run --locked --project . ruff format --check scripts
uv run --locked --project . python scripts/check_i18n.py --root .
./scripts/build_site.sh
```

校验器会从脚本位置推导仓库根目录，检查双语路径/配置、front matter 与安全 tags、人物页结构、`list.yaml`/`list.md`、字母 `index.md` 链接、本地 Markdown 目标、原始 HTML/事件属性、危险或 HTTP 协议、未定义数字引用、未转义 `$`、IAFD 首页和 Wikipedia Draft 等来源问题；同时比较 URL/handle、身高/体重、作品数量、百分比和 `万/亿` 数量级。先修复所有校验错误，再继续构建。

`./scripts/build_site.sh` 会从自身位置推导仓库根目录，在 `uv run --locked` 环境中执行校验，再在 staging 目录中以锁定的 Zensical 0.0.62 分别执行中文和英文的 `--clean --strict` 构建；成功后才替换 `site/`，并复制 `LICENSE`/`NOTICE`。需要诊断时可分别运行：

```bash
uv run --locked --project . zensical build --config-file zensical.toml --clean --strict
uv run --locked --project . zensical build --config-file zensical.en.toml --clean --strict
git diff --check
```

英文版是机器翻译初稿，不是自动事实核查。提交前必须由人工：

- 对照中文源检查专有名词、标题、术语、语法、代词和身份表述；
- 对照公开来源复核数字、日期、作品数量、奖项、来源标题、URL 和 handle；
- 检查敏感信息是否有必要、是否公开且有来源支持；
- 确认没有把模型猜测写成“已核实”。

校验器和 strict 构建验证的是结构、安全与双语一致性，不会验证外部链接是否可访问、来源内容、事实、翻译质量或奖项时效性。构建成功后仍应在交付说明中明确英文是否完成人工复核。

提交信息沿用仓库风格，但**默认不要自动提交**；只有用户明确要求时才提交：

- 单个：`add: <艺名> entry - <一句话描述>`
- 多个：`add: <A> + <B> - <描述>`
- 示例：`add: Chanel Noir entry (transgender actress, Grooby/Evil Angel)`、`add: Izzy Wilde (Zoe Summers) entry - trans performer, AVN winner`

只提交源文件（条目 `.md`、字母 `index.md`、相关元数据）；如果本次确实改变依赖，还要一并审阅并提交 `pyproject.toml` 与 `uv.lock`，不要手改 lock 文件。不要提交 `site/`。中文行文沿用现有条目的全角标点和 `**字段**: 值` 概要格式；英文按人工校订结果书写，不要把机器直译当作最终文案。不要删除或改写其他演员条目，除非用户明确要求；信息无法核验时写“未公开/未确认”，宁可降低 completeness 也不编造。
