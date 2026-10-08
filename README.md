# skills-hep

面向高能物理研究的 Skills 插件集合。当前包含 `hep-scientific-plotting`，负责消费上游最终结果，生成和审查 DELPHI 科研图。

## 本地导入

```bash
codex plugin marketplace add /absolute/path/to/skills-hep
codex plugin add skills-hep@skills-hep
```

在桌面插件目录中选择 HEP Skills 来源并安装 skills-hep。目录清单用于自定义来源，不代表已上架官方公共商店。

## 内容与依赖

- `skills/hep-scientific-plotting/SKILL.md`：入口及任务边界。
- `plugin.json`：插件身份和版本。
- `.agents/plugins/marketplace.json`：目录来源及插件入口。

项目提供分析环境和 DataFactory。渲染及几何检查使用 Matplotlib、mplhep 和 NumPy；纯静态检查使用 Python 标准库。插件不安装这些依赖，也不打包 DataFactory。

## 检查

在已有绘图环境中运行：

```bash
python -m unittest discover -s skills/hep-scientific-plotting/scripts -p 'test_*.py'
```

当前项目使用新的 Git 历史，不继承原单 Skill 仓库；尚未配置远程。分析项目中的旧 Skill 路径以本地软链接保留，软链接不属于分发包。
