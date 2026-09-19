# 成人影片演员百科 / Adult Film Performer Encyclopedia

本仓库使用 Zensical 构建中英双语人物资料型百科。中文内容位于 `docs/zh/`，英文内容位于 `docs/en/`；两个目录使用相同的相对路径。

This repository uses Zensical to build a bilingual Chinese-English encyclopedia. Chinese content lives in `docs/zh/`, English content in `docs/en/`, and matching pages use the same relative path.

翻译所用模型、实测速度、质量限制与维护流程见 [TRANSLATION.md](TRANSLATION.md)。

## 本地构建

```bash
./scripts/build_site.sh
```

生成的 `site/` 为构建产物，不纳入版本控制（见 `.gitignore`）。现有中文版 URL 保持不变，英文版发布在 `/en/`，并可通过页眉语言选择器切换。

To preview one language while editing, run `zensical serve --config-file zensical.toml` for Chinese or `zensical serve --config-file zensical.en.toml` for English.

## 内容约定

- 人物资料应附可核验的公开来源。
- 对本名、出生日期、性取向等敏感信息，应避免采用无法可靠核验的说法。
- 会随时间变化的数据应注明核验日期。
- 新增或删除人物文件后，应同步维护相应字母目录的 `index.md`。
- 每次内容变更应同步更新 `docs/zh/` 与 `docs/en/`；`python3 scripts/check_i18n.py` 可检查文件是否一一对应。
