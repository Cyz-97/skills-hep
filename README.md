# skills-hep

面向高能物理研究的 Skills 插件集合，覆盖科研绘图、文献调研和学术写作。

## Skill 成员

| 成员 | 用途 | 入口与说明 |
|---|---|---|
| `hep-scientific-plotting` | 消费上游最终结果，生成和审查 DELPHI 科研图 | [Skill 入口](skills/hep-scientific-plotting/SKILL.md) |
| `academic-writing-studio` | 文献比较与证据综合，按 Article、Letter、综述等文体起草、修改和核验稿件，支持 HEP | [Skill 入口](skills/academic-writing-studio/SKILL.md) · [用法与案例](skills/academic-writing-studio/README.md) |

写作成员包含文体默认语言与一次语言确认、中文粒子物理词目索引、轻量语言编辑及审稿修订指引。已有语言要求直接沿用；专业术语按需查阅。

## 本地导入

```bash
codex plugin marketplace add /absolute/path/to/skills-hep
codex plugin add skills-hep@skills-hep
```

在桌面插件目录中选择 HEP Skills 来源并安装 skills-hep。目录清单用于自定义来源，不代表已上架官方公共商店。

## 内容与依赖

- `skills/hep-scientific-plotting/SKILL.md`：入口及任务边界。
- `skills/academic-writing-studio/SKILL.md`：文体、语言和本轮写作任务入口。
- `plugin.json`：插件身份和版本。
- `.agents/plugins/marketplace.json`：目录来源及插件入口。

绘图成员使用项目提供的分析环境和 DataFactory。渲染及几何检查使用 Matplotlib、mplhep 和 NumPy；纯静态检查使用 Python 标准库。插件不安装这些依赖，也不打包 DataFactory。

写作成员由 Markdown 指引、参考和模板组成，无额外运行依赖。实际检索、文献读取或稿件核验使用当前环境可用的工具，并如实记录访问范围。原始书籍全文与个人工作记录不在插件包中。

## 开发验证

以下测试用于修改 Skill 的检查工具后验证实现，普通绘图不要求运行 linter 或几何检查器：

```bash
python -m unittest discover -s skills/hep-scientific-plotting/scripts -p 'test_*.py'
```

源仓库：[Cyz-97/skills-hep](https://github.com/Cyz-97/skills-hep)。成员在本仓库的 `skills/<skill-name>/` 目录维护；项目内不保留同名 Skill 副本或软链接。开发时全局 Skill 入口可链接到相应成员目录，软链接不属于分发包。

绘图成员默认首次实际渲染后查看结果，科学表达正确、可读且无关键遮挡即结束；布局建议不作为反复迭代门槛。空分母比值、错误归一化等科学风险仍需核对。

## 来源与许可

仓库自有代码的许可见 [LICENSE](LICENSE)。成员中的第三方改编内容保留其来源与许可；写作成员的 ARS 改编部分为 CC BY-NC 4.0，开放书籍改编部分为 CC BY 4.0，具体归属、范围及原文访问状态见[写作来源目录](skills/academic-writing-studio/references/sources.md)。
