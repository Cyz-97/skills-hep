# skills-hep

面向高能物理研究的 Skills 插件集合，覆盖科研绘图、文献调研和学术写作。

## 按任务选择成员

| 你的任务 | 使用成员 | 详细说明 |
|---|---|---|
| 已有最终结果，需要绘制或审查 DELPHI 科研图 | `hep-scientific-plotting` | [任务边界与绘图指引](skills/hep-scientific-plotting/SKILL.md) |
| 需要比较论文、综合证据，或起草、修改和核验学术稿件 | `academic-writing-studio` | [用法与案例](skills/academic-writing-studio/README.md) · [文体与任务入口](skills/academic-writing-studio/SKILL.md) |

## 安装与首次使用

### Codex

在已配置 GitHub SSH 访问的环境中，将本仓库加入 Codex 的插件来源：

```bash
codex plugin marketplace add git@github.com:Cyz-97/skills-hep.git --ref main
```

重启桌面应用，在插件目录中选择 **HEP Skills** 来源并安装 **skills-hep**，然后开启新会话。该来源由本仓库维护；安装流程见 [OpenAI 官方说明](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)。

### ZCode

打开工作区，在 **Settings → Plugins → Create → Add marketplace** 添加 `Cyz-97/skills-hep`（也可填写本仓库的 HTTPS URL），然后安装并启用 `skills-hep`。

已添加来源时，先在 **Marketplace sources** 中刷新该来源，再检查插件更新。仓库提供根目录的 `marketplace.json` 与 `.zcode-plugin/plugin.json`，供 ZCode 发现和安装；[安装及更新说明](https://zcode.z.ai/en/docs/plugin)。

### 首次调用

提供相应材料后，可直接使用以下提示词。ZCode 中可输入 `/` 并从 Skills 列表选择对应成员，再描述任务。

绘图：

```text
使用 $hep-scientific-plotting，根据我提供的最终直方图和误差，
绘制 DELPHI 风格的 Data/MC 主图和 ratio。
保持归一化与误差定义，交付 PDF、caption 和代码。
```

写作：

```text
使用 $academic-writing-studio，基于我提供的论文规划一篇 HEP 技术综述。
比较研究问题、方法和结果，按默认语言交付提纲与证据缺口。
```

## 依赖概览

- **绘图成员：** 使用项目提供的分析环境和 DataFactory；渲染与几何检查使用 Matplotlib、mplhep 和 NumPy，纯静态检查使用 Python 标准库。插件不安装这些依赖。
- **写作成员：** 由 Markdown 指引、参考和模板组成，无额外运行依赖；实际检索、文献读取与核验使用当前环境可用的工具。原始书籍全文与个人工作记录保留在用户材料中。

## 开发入口

成员在 `skills/<skill-name>/` 目录维护，具体任务规则在各成员文档中更新。发布时同步根 `plugin.json`、`.zcode-plugin/plugin.json` 与根 `marketplace.json` 插件条目的版本；Codex 的市场入口保留在 `.agents/plugins/marketplace.json`。开发时可将本地仓库加入插件来源：

```bash
codex plugin marketplace add /absolute/path/to/skills-hep
```

修改绘图成员的检查工具后，从仓库根目录运行其测试：

```bash
python -m unittest discover -s skills/hep-scientific-plotting/scripts -p 'test_*.py'
```

## 来源与许可

仓库自有代码的许可见 [LICENSE](LICENSE)。成员中的第三方改编内容保留其来源与许可；写作成员的 ARS 改编部分为 CC BY-NC 4.0，开放书籍改编部分为 CC BY 4.0，具体归属、范围及原文访问状态见[写作来源目录](skills/academic-writing-studio/references/sources.md)。
