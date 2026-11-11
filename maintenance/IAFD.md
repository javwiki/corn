# IAFD 作品资料核对

2026-11-11 依照 `~/agent/skills/webtop/SKILL.md`，通过 CDP 连接 webtop 的现有 Chromium，在自行新开的标签页中读取搜索、演员片目和作品页；使用完毕关闭自建标签页。没有修改用户原有标签页、登录状态或浏览器出口。

共匹配 22 个作品条目。仅保存所用事实、来源链接与简短改写的剧情简介，不将原站 HTML 或整段简介提交到仓库。

| 条目 ID | 原始 CSV 记录 | IAFD 作品页 |
| --- | --- | --- |
| work-002 | 2 | [IAFD](https://www.iafd.com/title.rme/id=46131b50-65ec-4264-99f2-3f1d63724b83) |
| work-003 | 3 | [IAFD](https://www.iafd.com/title.rme/id=29b8ce65-fbcc-43a6-984d-0187132f9ab7) |
| work-004 | 4 | [IAFD](https://www.iafd.com/title.rme/id=d379fdc1-d8b7-4981-a489-b927fb5a1230) |
| work-005 | 5 | [IAFD](https://www.iafd.com/title.rme/id=c493229b-a188-4e48-8be0-dc86e6329590) |
| work-006 | 6 | [IAFD](https://www.iafd.com/title.rme/id=c99d86db-7268-4ea6-bfa4-54b97e2e24ad) |
| work-007 | 7 | [IAFD](https://www.iafd.com/title.rme/id=8c07ba87-3498-494f-b000-ce3a67726e12) |
| work-008 | 8 | [IAFD](https://www.iafd.com/title.rme/id=a5d1a798-e178-4855-941c-982e1eda35e6) |
| work-009 | 9 | [IAFD](https://www.iafd.com/title.rme/id=9fc37296-e126-4581-9cfd-a7701e10444b) |
| work-010 | 10 | [IAFD](https://www.iafd.com/title.rme/id=7b00b819-a198-47f9-834c-7f7fa96966b7) |
| work-011 | 11 | [IAFD](https://www.iafd.com/title.rme/id=88ac8b30-b198-49b5-b695-ba7f694c88f4) |
| work-012 | 12 | [IAFD](https://www.iafd.com/title.rme/id=0ffe4830-8905-41d9-a310-fa478395bb9d) |
| work-013 | 13 | [IAFD](https://www.iafd.com/title.rme/id=abaf31b2-874a-49d1-b678-08d2a0f101fb) |
| work-014 | 14 | [IAFD](https://www.iafd.com/title.rme/id=904656d7-b70c-4843-a7c3-704d8ac3caff) |
| work-016 | 16 | [IAFD](https://www.iafd.com/title.rme/id=bad56d35-48fb-4878-aec8-15515aeaf727) |
| work-018 | 18 | [IAFD](https://www.iafd.com/title.rme/id=e73386a5-2b48-4c1c-8bf9-10fbf1693939) |
| work-020 | 20 | [IAFD](https://www.iafd.com/title.rme/id=00b38fdb-270f-47fb-9b2a-ab0fce9e950d) |
| work-021 | 21 | [IAFD](https://www.iafd.com/title.rme/id=1fc0ece7-d9d6-4871-b49d-8646c3a41ee7) |
| work-022 | 22 | [IAFD](https://www.iafd.com/title.rme/id=342cf613-6ee8-4ae8-977a-0bde59f26c20) |
| work-023 | 23 | [IAFD](https://www.iafd.com/title.rme/id=fff7dc3b-a532-4ab9-a94b-47cd806e897e) |
| work-024 | 24 | [IAFD](https://www.iafd.com/title.rme/id=c1f151fd-2543-4e98-989e-ac2d5b9ccab0) |
| work-025 | 25 | [IAFD](https://www.iafd.com/title.rme/id=a11222d6-ceea-412a-9664-99a049c65929) |
| work-026 | 26 | [IAFD](https://www.iafd.com/title.rme/id=36a44c2c-7610-43b3-a531-a0f0d6c29623) |

## 匹配与取舍

- `work-026`：先从 Mae Olsen 的片目找到场景，再核对作品页 `Comments` 中的 `Scene Code: MS11362`。厂牌为 `milfsoup.com`，演员包括 Ava Addams、Mae Olsen，与原文件名吻合；改用作品页正式标题。没有把合集《MILF Soup 28》的整片片长用于该网络场景。
- `work-012`、`work-018`：IAFD 将片中署名 Vivian Fox 的演员关联到 person ID `0d43f26d-6f4f-45d3-9e40-032b540b4376`，与仓库 `Vivian_Foxx.md` 的 IAFD 链接相同。因此作品演员链接使用 Vivian Foxx，署名单列。`work-012` 中 Ike Diezel 的出演由已有 XBIZ 报道支持。
- `work-011`：同名《Angel Tits》有 2018、2019 年等不同作品，采用演员为 Skylar Vox、Peter Green，厂牌为 Titty Attack 的 2019 年条目。
- `work-006`：同名搜索命中多部作品，按 Skylar Vox、Jax Slayher、2020-02-06 匹配；IAFD 区分发行方 `blacked.com` 与工作室 `blackedraw.com`。
- `work-016`：官方作品页为 47 分钟，IAFD 为 48 分钟，保留官方值。其他官方页面的精确分秒数也不被数据库整数分钟覆盖。
- 原始 CSV 的全部 27 行仍完整保留；`work-017` 继续承接第 17、27 行的 Cosmid 记录。

## 未采用的结果

- `work-001`：完整片名、单数变体和关键词检索未找到可对应的 IAFD 页，保留原有 FlickList 资料。
- `work-015`：完整片名、较长标题变体、Truth or Dare 搜索和 Skylar Vox 片目中均未找到唯一对应。发现另一部 2022 年 TabooHeat 场景，但标题不同，不能据相同演员直接移用其日期、片长或简介。
- `work-017`：未找到对应 Cosmid 作品的 IAFD 页，保留官方 Cosmid 和已有 IMDb 资料。
- `work-019`：原记录只有演员和 POV Life 标签，无法仅凭其名字与 `work-012` 判为同作；不补猜信息。
