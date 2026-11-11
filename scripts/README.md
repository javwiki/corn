# 维护脚本

从仓库根目录运行：

```bash
uv run --locked python scripts/content/generate_works.py
uv run --locked python scripts/content/generate_navigation.py
uv run --locked python scripts/checks/check_i18n.py
uv run --locked python -m unittest discover -s tests -v
./scripts/build_site.sh
git diff --check
```

- `checks/check_i18n.py`：校验双语公开内容与维护资料、分类路径、人物 front matter、名单覆盖、字母索引、链接、安全约定和构建配置。默认从脚本位置定位仓库，也可通过 `--root` 指定。
- `content/generate_works.py`：将 `maintenance/works.yaml` 中逐字段标注出处的研究记录与原始 `scene.csv` 装配为双语作品页和目录。`--check` 检查生成内容漂移，并校验原始记录覆盖、资料状态及字段出处；完整构建与 CI 均会运行。
- `content/generate_navigation.py`：从英文页面标题生成 `zensical.toml` 的导航，分类显示英文名称，链接保留双语共享路径。新增、移动或修改英文页面标题后运行；完整构建通过 `--check` 检查导航是否同步。
- `build_site.sh`：从任意工作目录调用，运行 Ruff 和文档校验，在暂存目录严格构建英文、中文站点，验证入口和 404，复制许可证后替换 `site/`。失败时保留上一份产物；CI 继续使用同一入口。

内容结构见 [维护资料](../maintenance/README.md)。
