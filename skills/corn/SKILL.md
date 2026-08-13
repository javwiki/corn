---
name: corn-add-entry
version: 1.0.0
description: "成人影片演员百科（本仓库 /root/corn）新增人物条目。当用户要求添加演员/新人、收录某位表演者、新增条目、把某某加入百科时使用。覆盖：信息核验、创建 src/<首字母>/<艺名>.md 条目文件、同步字母目录 README.md、同步 src/_meta/list.yaml 与 src/_meta/list.md。不负责：标签页/_tags 与 SUMMARY.md（CI 自动生成）、删除条目（可参考 git 历史 7e887c8）。"
metadata:
  requires:
    bins: ["git"]
---

# 添加条目（corn 百科）

**CRITICAL — 动手前 MUST 先运行 `git -C /root/corn status` 与 `git -C /root/corn log --oneline -5`，确认工作区干净、了解最近提交风格。**

## 适用场景

- "给百科添加 XX"
- "新增演员 XX 的条目"
- "把 XX 收录进去" / "XX 能加进百科吗"
- 用户给出演员名（常见于 avn 获奖者、trans 表演者、IAFD 有记录者）

## 项目结构（只改这些）

```
src/<字母>/<艺名>.md      ← 条目文件（核心产物）
src/<字母>/README.md      ← 字母目录列表，需同步
src/_meta/list.yaml       ← 条目数据源（含 completeness），需同步
src/_meta/list.md         ← 人类可读列表，需同步（新条目加在最前面）
src/SUMMARY.md            ← CI 生成，禁止手动改
src/_tags/                ← CI 生成，禁止手动改
src/_meta/award/README.md ← CI 生成，禁止手动改
```

## 工作流

```
演员名 ─┬─► 信息核验（IAFD / Wikipedia / 官网 / 社交账号）──► 确定字母与文件名
        │
        ├─► 创建 src/<字母>/<艺名>.md（frontmatter + 概要 + 详情 + 参考资料）
        ├─► 更新 src/<字母>/README.md
        ├─► 更新 src/_meta/list.yaml（含 completeness 评分）
        ├─► 更新 src/_meta/list.md（最前面插入一行）
        └─► 可选本地校验 mdbook build ──► git commit
```

### Step 1: 信息核验（先查证，再动笔）

- 以 **IAFD**（iafd.com）为准核对作品数量、活跃年代；Wikipedia / Wikidata 核对出生、国籍、职业。
- 官网与公开社交账号（X/Twitter、Instagram、OnlyFans、ManyVids、Fansly、TikTok、Bluesky）确认平台。
- 信息不足时如实标注，**不要编造**（如"别名: 无记录"、"出生: 未公开"、"活跃年代: 未知 – 至今"）。
- 会随时间变化的数据（作品数、活跃状态）注明核验口径，如"IAFD 记录至 2025"。

### Step 2: 确定字母目录与文件名

- 按**艺名首字母**分目录：`Sky Bri` → `src/S/Sky_Bri.md`；`Bridgette B` → `src/B/Bridgette_B.md`。
- 文件名 = 艺名以 `_` 连接（空格→下划线，无其他特殊符号），若对应字母目录不存在则新建。
- 跨性别演员同样按当前艺名首字母，不按本名。

### Step 3: 创建条目文件

按下面模板写，字段可按实际情况增删（完整条目可加身高/体重/三围/发色等）：

```markdown
---
tags:
- pornstar
- Adult Actress
- <国籍，如 American / Australian / Japanese / South Korean>
- <身材/发色，如 Big Tits / petite / blonde>
- <主要制片公司，如 Brazzers / Blacked / Grooby>
- <平台，如 OnlyFans / ManyVids>
- <奖项，如 AVN / AVN Hall of Fame / XBIZ>
# 跨性别演员必须加：
- transgender
---

# <艺名>

## 概要

- **名称**: <艺名>
- **别名**: <别名，无则写"无记录">
- **平台**: OnlyFans / Twitter / Instagram（有哪个写哪个，无则"未指定"）
- **出生**: YYYY年M月D日，<国家>（信息不可靠则写"未公开"）
- **活跃年代**: YYYY –至今（或 YYYY –YYYY）
- **作品数量**: N 部（来源：IAFD / FreeOnes）
- **职业**: 色情女演员<、模特、导演、内容创作者等>
- **备注**: <一两句亮点：签约公司、奖项、成名作>

## 详情

<3-5 段生平与职业生涯，附可核验来源；涉奖项可加子表：

### 奖项与提名

| 年份 | 奖项 | 类别 | 结果 |
|---|---|---|---|
| ... | AVN Awards | ... | 获奖/提名 |
>

## 参考资料

- [<艺名> - Wikipedia](https://en.wikipedia.org/wiki/...)
- [<艺名> - IAFD](https://www.iafd.com/person.rme?id=...)
- [X/Twitter: @handle](https://x.com/handle)
- [Instagram: @handle](https://www.instagram.com/handle/)
- [OnlyFans](https://onlyfans.com/...)
```

**tags 规范**（对齐 2026-07 的标签规范化约定）：
- `pornstar`、`Adult Actress` 必带；国籍、发色/身材、制片公司、平台、奖项按实添加。
- **不要**加具体作品/片名场景标签（此前已清理），不要自造与现有风格不符的大小写（参考已有条目如 `Big Tits`、`blonde`、`webcam-model`、`content-creator`、`cosplayer`）。
- 敏感信息（本名、出生日期、性取向）只写可核验来源支持的，且注明出处。

**内容约定**（README 明确要求）：
- 资料附可核验的公开来源链接。
- 会随时间变化的数据注明核验日期/口径。

### Step 4: 更新字母目录 `src/<字母>/README.md`

- 若该目录 README 是简单格式（`# 字母 X 的演员` + 链接列表），把新链接按名字字母序插入，如：
  `- [<艺名>](<艺名>.md)`
- 若该目录 README 是完整格式（含 `## 概要`/演员数量统计，如 A/README.md），**同步更新演员数量**并插入列表。
- 新建字母目录时创建 README，参照最新提交中的简单格式。

### Step 5: 更新 `src/_meta/list.yaml`

- 在对应字母分组内按名字字母序插入（对齐既有提交做法）：

```yaml
- completeness: <评分>
  name: <艺名>
  file: <X>/<艺名>.md
  index: <X>
```

- **completeness 评分标准**：
  - 100%：概要字段完整（出生/别名/平台/活跃年代/作品数量/职业/备注）+ 详情充分 + 多个参考资料
  - 90-95%：概要齐全但详情或参考资料略少；跨性别/小众演员信息完整度较高者
  - 70-85%：信息有明显缺口（无出生、无作品数、来源单一）
  - 参考存量：Skylar Vox 100%、Asuka Tenshi 45%、Piper Perri 70%、Abigail Lust 75%

### Step 6: 更新 `src/_meta/list.md`

- 在 `# 成人影片演员列表` 标题后**最前面**插入一行（保持"最近新增在前"）：

```markdown
- **<艺名>** (<X>) - 完成度: <评分>%
```

### Step 7: 校验与提交

- 若本机装有 mdbook 工具链，可本地验证（生成物均在 .gitignore，可安全丢弃）：
  `mdbook-tagging generate . && mdbook-summarizer --src src --auto-readme && mdbook build`
- 提交信息沿用仓库风格：
  - 单个：`add: <艺名> entry - <一句话描述>`
  - 多个：`add: <A> + <B> - <描述>`
  - 示例：`add: Chanel Noir entry (transgender actress, Grooby/Evil Angel)`、`add: Izzy Wilde (Zoe Summers) entry - trans performer, AVN winner`
- 只提交源文件（条目 .md、字母 README、list.yaml、list.md），**不要**提交 SUMMARY.md、src/_tags/、book/。

## 反例 / 注意事项

- 不要手动改 SUMMARY.md 或 _tags/（CI 用 mdbook-tagging + mdbook-summarizer 生成）。
- 不要删除/改写其他演员条目，除非用户明确要求。
- 信息无法核验时写"未公开/无记录"，宁可降低 completeness 也不编造。
- 中文行文与现有条目一致（全角标点、`**字段**: 值` 的概要格式）。
