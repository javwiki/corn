# 维护资料与目录结构

本项目参照 `javwiki.github.io` 将公开百科、维护资料和脚本分开。双语使用相同相对路径，英文仍是默认语言。

```text
docs/{en,zh}/
├── index.md
├── 人物/
│   └── 演员/{字母}/{艺名}.md
├── 作品/
│   ├── index.md
│   └── 单部/{作品}.md    # 双语独立作品／待识别记录
├── 资料/
│   └── 奖项/
│       ├── index.md
│       ├── awards.md
│       └── award-winners.md
└── 专题/index.md
maintenance/
├── README.md
├── TRANSLATION.md
├── scene.csv
├── works.yaml            # 作品研究记录、逐字段出处和原始行映射
└── {en,zh}/
    ├── index.md
    ├── list.md
    ├── list.yaml
    ├── source.yaml
    └── award-winners-todo.md
scripts/
├── README.md
├── build_site.sh
├── checks/check_i18n.py
└── content/generate_works.py
```

人物统一使用「演员」分类，保留现有的艺名首字母索引；两种语言共享中文分类路径。分类及字母目录均使用 `index.md` 作为入口。作品目录已根据原 `scene.csv` 建立；产业等分类在有实际内容时再增设。

`maintenance/` 不参与站点发布，名单、来源登记、翻译记录、待补条目和原始场景清单保留在此。`list.yaml` 的 `file` 字段相对于 `docs/{lang}/`，例如 `人物/演员/A/Angela_White.md`；`list.md` 随条目手动维护。校验器仍检查维护资料的双语文件集合、Markdown 链接、名单覆盖和双语一致性。

本次迁移不保留旧 URL 重定向，人物地址改为 `/corn/人物/演员/{字母}/{艺名}/`，中文在 `/corn/zh/` 下使用相同路径。公开页面只链接公开内容，维护资料可通过仓库查看。

新增、移动或删除条目时，同步修改双语条目、字母索引、演员目录和维护名单；新增字母目录时也需同步更新演员目录。验证命令见 [脚本文档](../scripts/README.md)，翻译约定见 [TRANSLATION.md](TRANSLATION.md)。

## 作品资料

`scene.csv` 保留原始 27 条记录。`works.yaml` 将它们对应到 26 个独立条目；第 17、27 条根据 Cosmid、演员、Workout 与日期线索归并，未核验原视频文件内容或版本。原始 CSV 不据此重写。

检索日期为 2026-11-11。当前 26 个条目中，22 个通过 webtop Chromium 实际访问 IAFD 作品页补充资料，另有 2 个保留其他出处，2 个尚未唯一匹配。20 个条目已有双语剧情简介。核对记录见 [IAFD.md](IAFD.md)。

公开页只显示已有资料、剧情简介和参考来源，不展示检索状态、核验过程、原始文件名和检索日期。缺少字段或简介时直接省略；`search_leads` 和 `notes` 仅保留在维护文件中。

- IAFD 用具体作品页作为出处，按标题、年份、演员、厂牌或场景编号匹配；同名作品不直接合并。
- `studio` 和 `distributor` 分别保存厂牌／工作室与发行方，不据此推定法人关系。数据库没有提供导演时不填。
- 片长有官方来源时保留官方精度；IAFD 的整数分钟不覆盖官方的分秒数。日期采用 `RELEASE DATE`，不把录入数据库的日期当作首发日期。
- 转载、下载帖和用户评论只作为检索线索，不作为事实出处。近似片名、其他场景或文件名中的日期不代替作品证据。

维护时先编辑 `works.yaml`，为每个事实字段指定来源数组中的下标；仅有原始清单线索的记录保持 `unresolved`。未知编号、版本、片名关系要写清限制。然后执行：

```bash
uv run --locked python scripts/content/generate_works.py
uv run --locked python scripts/content/generate_navigation.py
./scripts/build_site.sh
```

`docs/{en,zh}/作品/index.md`、`作品/单部/index.md` 和单部页面由同一份研究记录生成；不要直接修改生成页。生成器要求原始 CSV 的每条记录恰好映射一次，构建时用 `--check` 检测漂移。

剧情简介采用 `synopsis: {zh: ..., en: ..., source: 0}` 保存中英文正文及出处下标。只概括来源中的故事设定，不根据片名补写剧情；缺少简介时不生成该章节。报道日期不属于作品资料，不在作品页显示。
