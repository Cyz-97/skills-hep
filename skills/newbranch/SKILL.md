---
name: newbranch
description: 用户调用 newbranch 或要求开始新功能、排错、测试代码开发时，创建并切换到 feature/、debug/、test/ 等任务分支；项目内容只读，仅操作 Git。
---

# 创建任务分支

先读[Git 运维共同边界](../clear-git/references/git-boundaries.md)。此入口只准备分支；后续实现或运行测试属于用户另行授权的开发工作。

## 参数与命名

`newbranch [任务描述或完整分支名] [基点]`。对话中的 `$newbranch` 是 skill 调用，不是 shell 可执行程序。

- 新功能：`feature/<简短主题>`。
- 排错或修复：`debug/<简短主题>`。
- 测试代码开发：`test/<简短主题>`；文档或重构可用 `docs/`、`refactor/`。
- 主题采用小写英文 kebab-case，描述具体任务；不自动添加 `codex`、`ai`、`agent` 等来源标识。用户明确给出完整名称时校验并沿用；与该命名要求冲突时请其指定符合要求的名称。
- 基点优先使用用户明确给出的 ref；未指定时使用调用前的当前 HEAD。不擅自改从 master/main/dev 开始，也不自动 fetch/pull。

## 执行

1. 按共同边界完成执行环境检查；用 Git 确认仓库、当前分支、HEAD、工作区状态与 `git worktree list --porcelain`。已有 merge/rebase/cherry-pick、未解决冲突时暂停。任务意图或基点从会话已明确时直接使用；均缺失时只问缺项。
2. 根据任务确定分支名，用 `git check-ref-format --branch <分支名>` 校验；确认基点可解析为 commit。检查本地及已知远端同名 ref，存在时保留原分支，不用 `-C` 覆盖。
3. 当前未提交改动属于本任务且普通 switch 能安全保留时，带入新分支；来源不清时先问归属。不给这些改动自动提交、stash 或清空。detached HEAD 可用已确认的当前提交作基点。
4. 使用 `git switch --no-track -c <分支名> <基点>` 创建并切换，沿用共同边界的命令前缀。Git 因文件覆盖、其他 worktree 或过滤器拒绝操作时报告并停止，不强制继续。
5. 用 Git 核对当前分支、HEAD 与基点一致，以及原有暂存、未暂存和未跟踪内容保留。报告分支名、基点 hash、带入的改动和下一步可使用的 `clear-git`、`mergeto <目标分支>`。

**完成条件：** 新任务分支已检出，原有改动完整保留；此入口尚未开发、运行脚本或测试，也未推送远端。
