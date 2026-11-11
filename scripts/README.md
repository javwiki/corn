# 维护脚本

从仓库根目录运行：

```bash
uv run --locked python scripts/checks/check_i18n.py
./scripts/build_site.sh
git diff --check
```

- `checks/check_i18n.py`：校验双语公开内容与维护资料、分类路径、人物 front matter、名单覆盖、字母索引、链接、安全约定和构建配置。默认从脚本位置定位仓库，也可通过 `--root` 指定。
- `build_site.sh`：从任意工作目录调用，运行 Ruff 和文档校验，在暂存目录严格构建英文、中文站点，验证入口和 404，复制许可证后替换 `site/`。失败时保留上一份产物；CI 继续使用同一入口。

内容结构见 [维护资料](../maintenance/README.md)。
