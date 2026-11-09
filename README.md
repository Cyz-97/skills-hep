# skills-hep

面向高能物理研究的 Skills 插件集合，覆盖分析脚本编写、架构与流程示意图、科研绘图、文献调研、学术写作和 Git 运维。

## 按任务选择成员

| 你的任务 | 使用成员 | 详细说明 |
|---|---|---|
| 编写或重构面向流程的 PyROOT / DataFactory 分析脚本 | `coding` | [计算分工与 PART+cell 写法](skills/coding/SKILL.md) |
| 用 Mermaid 表达代码架构、HEP 分析流程、样本成分或资源开销 | `diagram` | [选图规则与示例](skills/diagram/SKILL.md) |
| 已有最终结果，需要绘制或审查 DELPHI 科研图 | `hep-scientific-plotting` | [任务边界与绘图指引](skills/hep-scientific-plotting/SKILL.md) |
| 需要比较论文、综合证据，或起草、修改和核验学术稿件 | `academic-writing-studio` | [用法与案例](skills/academic-writing-studio/README.md) · [文体与任务入口](skills/academic-writing-studio/SKILL.md) |
| 开发前创建功能、排错或测试代码分支 | `newbranch` | [命名与建分支](skills/newbranch/SKILL.md) |
| 开发结束后按 commit type 整理提交，保留本地生成产物 | `clear-git` | [提交整理与产物处理](skills/clear-git/SKILL.md) |
| 将当前任务分支合入指定目标，并留下详细合并说明 | `mergeto` | [合并方向与提交正文](skills/mergeto/SKILL.md) |

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

示意图：`使用 $diagram，根据当前代码画出 Data 和 MC 从输入到物理结果的流程。`

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

- **分析脚本成员：** 复用项目的 PyROOT、DataFactory 和 Matplotlib 环境；模块自带一个合成示例。
- **示意图成员：** 提供 Mermaid 指引和四份可编辑示例；预览使用已有的 Mermaid 渲染器。
- **绘图成员：** 使用项目提供的分析环境和 DataFactory；渲染与几何检查使用 Matplotlib、mplhep 和 NumPy，纯静态检查使用 Python 标准库。插件不安装这些依赖。
- **写作成员：** 由 Markdown 指引、参考和模板组成，无额外运行依赖；实际检索、文献读取与核验使用当前环境可用的工具。原始书籍全文与个人工作记录保留在用户材料中。
- **Git 成员：** 仅依赖 Git；项目文件只读，不运行脚本、测试或构建。允许创建分支、暂存提交及合并等已授权的 Git 操作；[共同边界](skills/clear-git/references/git-boundaries.md)也约束 hooks、过滤器等隐式执行入口。

## Git 运维用法

在对话中按顺序调用，Codex 可用 `$` 选择技能，ZCode 可从 `/` 的 Skills 列表选择对应入口；这些名称无需安装为 shell 命令。

```text
$newbranch feature/photon-selection
$clear-git
$mergeto dev
```

`newbranch` 从当前 HEAD 或指定基点创建任务分支，使用 `feature/`、`debug/`、`test/` 等前缀，名称描述任务。`clear-git` 每种 commit type 在本轮最多提交一次；脚本生成的 JSON、ROOT、图片和 PDF 保留本地，源码与配置按实际用途识别。`mergeto dev` 表示当前分支合入 `dev`，使用 `--no-ff` 保留独立节点，正文记录动机、依据、原理、实现及验证限制。Git-only 范围内均不运行项目程序，也不代为编辑或解决源码冲突。

三者默认仅处理本地状态，保留来源分支和未确认可丢弃的内容。生成产物仍未跟踪或已有产物仍被修改时会如实报告；提交整理不保证 `git status` 完全为空。新分支准备完成后，实际开发需另行描述任务。

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
