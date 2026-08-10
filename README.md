# 成人影片演员百科

本仓库使用 mdBook 构建人物资料型百科。

## 本地构建

```bash
mdbook-tagging generate .
mdbook-summarizer --src src --auto-readme
mdbook build
```

生成的 `src/SUMMARY.md`、`src/_tags/`、`src/_meta/award/README.md` 与 `book/` 均为构建产物，不纳入版本控制（见 .gitignore）。

## 内容约定

- 人物资料应附可核验的公开来源。
- 对本名、出生日期、性取向等敏感信息，应避免采用无法可靠核验的说法。
- 会随时间变化的数据应注明核验日期。
- 新增或删除人物文件后，应同步维护相应字母目录的 `README.md`。
