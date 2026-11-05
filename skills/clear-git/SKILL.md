---
name: clear-git
description: 分析当前 Git 工作区，按 Conventional Commits 类型整理提交，每种 type 本轮最多一个 commit；保留本地生成产物。用于 clear-git、整理提交、提交开发成果或清理待提交改动。
---

# 整理 Git 提交

先读[共同边界](references/git-boundaries.md)。本 skill 只读项目内容，写入限于用户授权的 Git 操作。

## 入口

- `clear-git`：执行下面的提交整理。
- `newbranch [任务或分支名]`：读取 [newbranch](../newbranch/SKILL.md)，创建任务分支。
- `mergeto <目标分支>`：读取 [mergeto](../mergeto/SKILL.md)，将当前任务分支合入指定目标。

这些是对话中的 skill 入口，无需安装同名 shell 命令。

## 提交整理

1. 按共同边界完成 Git 执行环境检查，再读取 `git status --short --branch`、已暂存与未暂存 diff、未跟踪文件清单及近期提交。已暂存内容同样纳入分析；有未完成的 merge/rebase/cherry-pick 时先报告状态，暂停整理。
2. 根据路径、diff 和当前任务识别源码、文档、配置与生成产物。用 Git 只读查看必要内容；未跟踪文本可用 `git diff --no-index -- /dev/null <路径>` 查看，返回 1 表示有差异。
3. 列出“type → 功能分组 → 文件或 hunk”的提交方案，随后执行已授权的提交。每种 type 在本次调用中最多创建一个 commit，不按 scope 再拆同一 type；多个功能在同一提交的正文分别说明。没有对应变更的 type 不创建空提交。此规则是用户偏好，适用范围为本轮整理，历史提交保持原样。
4. 按实际意图选用 `feat`、`fix`、`refactor`、`perf`、`docs`、`test`、`build`、`ci`、`chore` 等类型。`test` 只表示提交已有测试代码，运行边界保持不变。标题采用 `<type>(<scope>): <说明>`，scope 可省略；破坏性变更按规范标注。标准见 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)。
5. 用明确路径或 hunk 暂存各组，避免 `git add .` 或 `git add -A` 混入产物。同一文件含多个 type 时用 Git 交互暂存分离；先盘点原有暂存，确保每次提交的 index 只包含当前组。若不能在本轮每种 type 一次的约束下可靠拆分，保留相关改动并说明阻碍。
6. 每次提交前检查 cached diff 的内容、路径和 `--check` 结果。提交正文说明各功能的目的与改动；项目验证写为“未运行脚本、测试或构建；仅审阅 diff 与 Git 状态”，已有结果可附来源，不能冒充本次验证。用 `git commit -m <标题> -m <正文>` 或标准输入传入消息，遵守共同边界中的无 hooks、无签名程序设置。
7. 最后用 Git 核对本轮 commit 的 type 无重复、内容与方案一致、当前分支及剩余改动。报告 hash、各提交用途、保留产物、未提交内容和实际 Git 检查结果。工作区仍有保留内容时明确说明。

## 生成产物

脚本生成的 `.json`、`.root`、`.png`、`.pdf` 及同类缓存或分析输出默认不提交，保留本地文件。按来源和用途判断：JSON 配置、测试 fixture、手写文档或用户明确指定版本化的资源可以提交，扩展名本身不决定删除或排除。

产物已暂存时，仅用 `git restore --staged -- <明确路径>` 取消暂存；首次提交无 HEAD 时可用 `git rm --cached -- <明确路径>` 保留文件。已跟踪产物的本地修改保留并报告，不用 restore 丢弃，也不擅自取消跟踪。已有 ignore 规则继续生效；本 skill 不改 `.gitignore` 或全局配置，也不通过隐藏状态制造“干净”结论。

**完成条件：** 本轮所有可归类、可安全提交的目标改动已处理，每种 type 最多一个提交，排除项保留且有清单。无可提交变更时报告即可。
