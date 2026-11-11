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

检索日期为 2026-11-11。11 个条目取得外部作品资料，其中 4 个有官方目录资料，其他来自数据库、行业报道或二手资料；15 个条目仍待核实。所有记录均有双语独立页，待核实记录不补猜演员、发行方或日期，公开页面明确说明资料限制。`search_leads` 保留清单检索线索，不是成功来源。

- 官方可核对的主要入口：Vixen、Blacked Raw、Naughty America 的作品页，以及 Cosmid 的 Dylan Voxe 更新目录。
- IMDb 部分条目只能从索引记录读取，直接访问时遇到 403 或验证页；相应限制写入作品页。没有把搜索命中或可访问的主页当作作品级核验。
- Reality Kings、Brazzers、Hookup Hotshot、Family Therapy 和 Net Video Girls 的相关入口未取得可用作品级资料；MYLF、TeamSkeet 和 PervMom 主要返回验证／推广页。没有绕过登录或验证，也没有将这些页面当作具体作品的证据。
- 转载、下载帖和用户评论只作为检索线索，不用作确认事实的出处。近似片名、其他场景或文件名日期不替代本作品证据。
- `reported` 是报道日期，不能代替 `release`；年月、年份和片长保留来源精度。发行标签不等同于制作公司法人。

维护时先编辑 `works.yaml`，为每个事实字段指定来源数组中的下标；仅有原始清单线索的记录保持 `unresolved`。未知编号、版本、片名关系要写清限制。然后执行：

```bash
uv run --locked python scripts/content/generate_works.py
uv run --locked python scripts/content/generate_navigation.py
./scripts/build_site.sh
```

`docs/{en,zh}/作品/index.md`、`作品/单部/index.md` 和单部页面由同一份研究记录生成；不要直接修改生成页。生成器要求原始 CSV 的每条记录恰好映射一次，构建时用 `--check` 检测漂移。
