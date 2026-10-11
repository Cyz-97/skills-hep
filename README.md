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

## 开发验证

以下测试用于修改 Skill 的检查工具后验证实现，普通绘图不要求运行 linter 或几何检查器：

```bash
python -m unittest discover -s skills/hep-scientific-plotting/scripts -p 'test_*.py'
```

源仓库：[Cyz-97/skills-hep](https://github.com/Cyz-97/skills-hep)。独立维护源位于本仓库；项目内不保留同名 Skill 副本或软链接。开发时全局 Skill 入口可链接到本仓库的 `skills/hep-scientific-plotting`，软链接不属于分发包。

默认首次实际渲染后查看结果，科学表达正确、可读且无关键遮挡即结束；布局建议不作为反复迭代门槛。空分母比值、错误归一化等科学风险仍需核对。
