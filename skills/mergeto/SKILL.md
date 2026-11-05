---
name: mergeto
description: 用户调用 mergeto 加目标分支时，将当前任务分支以 --no-ff 合入 dev、master、main 等明确目标，并在合并提交正文记录动机、依据、原理和实施过程；只操作 Git。
---

# 合入目标分支

先读[Git 运维共同边界](../clear-git/references/git-boundaries.md)。`mergeto <目标分支>` 表示 **调用时的当前分支 → 目标分支**；目标由用户给出，不按名称猜测。

## 准备合并

1. 按共同边界检查环境，记录当前来源分支及 source HEAD、目标分支及 target HEAD、工作区和 worktree 状态。来源必须是已确认的命名分支；来源与目标相同时报告无需合并。目标缺失或只存在远端时先确认，保留本地 ref；不自动创建主分支、pull 或 push。
2. 来源仍有未提交的源码、配置或文档时，报告并请用户先运行 `clear-git`；此入口不隐式整理提交。未跟踪或已忽略的生成产物可保留，但切换或合并可能覆盖它们时暂停。已有冲突或进行中的 Git 操作保持原状。
3. 用 `git merge-base <目标> <来源>` 找共同祖先，读取 `<基点>..<来源>` 的日志、diff 与提交正文，并对照目标侧差异。完整阅读当前会话提供的需求及已有设计依据；与实际变更交叉核对。整条分支的说明覆盖多次开发和多种 commit type，不局限最后一个提交。缺乏动机、理论依据或历史过程证据时明确标为“未记录/无法从 Git 历史确认”。
4. 若来源已经是目标的祖先，报告已包含，无需空合并；没有共同祖先时停止，保留现状。其余情况准备下方的详细提交说明，简短报告合并方向与范围后执行已授权的合并。

## 合并提交说明

标题采用 `chore(merge): merge <来源> into <目标>`。正文使用项目或会话语言，将以下内容填为具体事实；无依据的部分如实说明：

```text
Motivation
原始问题、使用场景、预期改善与本分支范围。

Basis and rationale
需求、issue/文献/设计记录或已有代码依据；实现原理、关键选择及其原因。
明确区分用户提供的依据、可从 diff 确认的行为和仍待确认的假设。

Implementation
按功能归纳主要改动、关键路径和可核对的提交；说明有记录的实施次序、
重要取舍与实际冲突处理。没有历史记录的过程标为未记录。

Verification and limitations
仅记录本次 Git diff、状态、包含关系及合并检查；未运行脚本、测试或构建。
既有验证记录注明来源和时间，无法证明当前状态时说明限制。
列出剩余问题、保留产物、兼容性影响及已知风险。

Merge scope
来源分支及 source HEAD；目标分支及合并前 target HEAD；共同祖先 hash。
```

## 执行与核对

1. 再次确认 source/target HEAD 未变化后，`git switch <目标分支>`。普通切换失败就停止，保留文件；目标在其他 worktree 检出时报告其位置，不强制接管。
2. 执行 `git merge --no-ff --no-commit --no-gpg-sign <来源>`，使用共同边界中的 Git 前缀及 `-c commit.gpgSign=false`。即使可 fast-forward，也保留单独的合并节点；保留分支原有提交。
3. 无冲突时用 Git 查看 pending merge diff、`git diff --cached --check` 和父节点引用，确认没有混入无关改动，再用 `git commit --no-gpg-sign -m <标题> -m <完整正文>` 写入上述说明，继续禁用 hooks 和外部签名程序。把各段正文作为一个完整参数或标准输入传入，保留真实换行。
4. 冲突发生时，用 `git diff --name-only --diff-filter=U` 列出路径，然后 `git merge --abort` 撤销本次合并并核对恢复状态。项目文件只读，因此不编辑冲突，不用 ours/theirs 丢弃任一侧。报告冲突、当前分支及后续所需的人工处理；abort 失败时报告现状，停在恢复现场。
5. 其他原因导致合并后尚未提交时报告 pending merge；若可安全撤销本次合并则用 `git merge --abort`，核对后报告。保留原有操作，遇到无法安全恢复的状态停止，禁止用 hard reset 兜底。
6. 成功后核对 merge commit 恰有两个父提交：第一父节点为记录的 target HEAD，第二父节点为 source HEAD；用 `git merge-base --is-ancestor <来源> HEAD` 确认包含关系。查看提交正文、Git 状态和保留产物，报告 merge hash、方向、摘要与限制。留在目标分支，保留来源分支，远端操作沿用共同边界。

**完成条件：** 目标分支上的合并节点、两个父节点和详细正文均核对一致；或已明确报告无须合并、缺项或冲突。功能测试状态始终如实说明。

依据：[Git merge](https://git-scm.com/docs/git-merge)。
