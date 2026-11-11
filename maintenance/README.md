# 维护资料与目录结构

本项目参照 `javwiki.github.io` 将公开百科、维护资料和脚本分开。双语使用相同相对路径，英文仍是默认语言。

```text
docs/{en,zh}/
├── index.md
├── 人物/
│   └── 演员/{字母}/{艺名}.md
├── 作品/index.md        # 原 scene.csv 中的作品与场景清单
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
└── {en,zh}/
    ├── index.md
    ├── list.md
    ├── list.yaml
    ├── source.yaml
    └── award-winners-todo.md
scripts/
├── README.md
├── build_site.sh
└── checks/check_i18n.py
```

人物统一使用「演员」分类，保留现有的艺名首字母索引；两种语言共享中文分类路径。分类及字母目录均使用 `index.md` 作为入口。作品目录已根据原 `scene.csv` 建立；产业等分类在有实际内容时再增设。

`maintenance/` 不参与站点发布，名单、来源登记、翻译记录、待补条目和原始场景清单保留在此。`list.yaml` 的 `file` 字段相对于 `docs/{lang}/`，例如 `人物/演员/A/Angela_White.md`；`list.md` 随条目手动维护。校验器仍检查维护资料的双语文件集合、Markdown 链接、名单覆盖和双语一致性。

本次迁移不保留旧 URL 重定向，人物地址改为 `/corn/人物/演员/{字母}/{艺名}/`，中文在 `/corn/zh/` 下使用相同路径。公开页面只链接公开内容，维护资料可通过仓库查看。

新增、移动或删除条目时，同步修改双语条目、字母索引、演员目录和维护名单；新增字母目录时也需同步更新演员目录。验证命令见 [脚本文档](../scripts/README.md)，翻译约定见 [TRANSLATION.md](TRANSLATION.md)。

## 作品清单

`scene.csv` 保留原始 27 条记录；双语公开入口为 `docs/{en,zh}/作品/index.md`。标题及文件名按源数据保留，`Present`、`Maker` 原本为空，未据标题猜测或补填。新增或修改作品时同步维护 CSV 与双语清单；将文件名整理为作品条目前需另行核验。
