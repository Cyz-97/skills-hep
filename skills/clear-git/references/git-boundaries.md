# Git 运维共同边界

适用于 clear-git、newbranch 和 mergeto；先读本页，再执行对应入口。

## 项目内容只读

- 只通过 Git 查看状态、差异、历史与内容；写操作限于请求所需的 index、commit、ref，以及 switch/merge 自身管理的工作树变更。
- 不运行项目或 skill 脚本、测试、构建、notebook、分析程序、格式化器或外部冲突解决器；不编辑源码、配置或生成产物。允许提交用户已经修改的这些文件。
- “测试代码已提交”“Git diff 无空白错误”“合并成功”各自描述实际结果，均不代表功能测试通过。只能引用已有测试记录并注明来源；没有记录时写“未运行”。
- 只有审阅请求时，停留在只读 Git 操作。创建技能或描述功能本身不授权对任意仓库执行提交、建分支或合并。

## 防止 Git 隐式执行项目程序

所有命令使用 Git 内建子命令。每次调用以 `git --no-pager -c core.hooksPath=/dev/null -c core.fsmonitor=false` 为前缀，避免 hooks 和 fsmonitor 启动程序；仅设置本次命令参数，保留仓库和全局配置。

进行 status/diff/add/switch/merge 前，用 `git config --show-origin --get-regexp` 有针对性检查 `filter.*`、`diff.*`、`merge.*`、`core.attributesFile`、`core.sshCommand` 等执行入口，并结合 `git ls-files`、`git check-attr` 判断候选路径。config 返回 1 可能只表示无匹配项；不要把凭据或含凭据的配置值写入报告。

- diff/show/log 读取 patch 时加 `--no-ext-diff --no-textconv`。
- commit/merge 加 `-c commit.gpgSign=false`，并使用 `--no-gpg-sign`，以免启动外部签名程序。报告提交未签名；仓库强制签名时报告限制并暂停写操作。
- 路径涉及 clean/smudge/process 过滤器、外部 merge driver 或其他外部执行入口时，先停止可能触发它们的操作。不要运行它们，也不要替换内容过滤器来强行提交；这可能改变实际入库内容。可继续执行不会触发这些入口的 Git 只读检查。
- 操作消息直接作为 Git 参数或标准输入传入，避免启动编辑器、执行消息中的 shell 展开或创建项目脚本。对用户提供的 ref 验证后作为单独参数传入，路径使用 `--` 分隔。

## 保留工作与授权范围

使用当前仓库的任务约定和已明确的来源、目标；不自动 stash、amend、rebase 或重写历史。不执行 `reset --hard`、`clean -f`、强制切分支或强制推送。删除文件、分支、worktree 与丢弃改动需要独立的明确请求；“清理工作区”只授权整理可提交改动。

默认仅处理本地 Git 状态。fetch/pull/push、发布和远端删除按本次任务的既有明确授权执行；`mergeto` 自身仅授权本地合并。发现需要新授权的外部操作时先完成本地范围并报告。

仓库规则要求测试、生成或修改源码才能继续时，说明当前 Git-only 边界下的缺项，保留状态并停止受影响的写操作。已有冲突或其他未完成操作不由本 skill 擅自清除。

依据：[Git hooks](https://git-scm.com/docs/githooks)、[Git diff](https://git-scm.com/docs/git-diff)、[Git merge](https://git-scm.com/docs/git-merge)。
