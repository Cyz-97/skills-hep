---
name: diagram
description: 用 Mermaid 展示现有或拟议的代码架构、HEP 分析流程、调用时序，以及样本成分、CPU 耗时和磁盘占用等简要数据。
---

# Mermaid 示意图

先确定图要回答的问题，再选图型：

| 问题 | 图型 |
|---|---|
| 数据经过哪些脚本，怎样变成物理结果？ | `flowchart TB`，读 [HEP 分析流水线](references/hep-pipeline.md) |
| 模块各自负责什么，依赖谁？ | `flowchart LR`，按职责分组，边注明依赖含义 |
| 一次运行中谁先调用谁、何时返回？ | `sequenceDiagram`，用时间顺序表达调用、返回和并行 |
| 类型、数据实体或状态间有什么关系？ | 类用 `classDiagram`，实体用 `erDiagram`，状态转移用 `stateDiagram-v2` |
| 样本由什么组成？各步骤资源用量如何？用量怎样随数据规模变化？ | 饼图、条形图或折线图，读 [简要数据图](references/chart-data.md) |
| 已知数量分别流向哪里？ | Sankey，边对应同单位、可加的流量 |

1. **取材。** 现状图从代码入口、配置和实际读写处取证；设计图标「拟议」，待定接口也标出。数据图注明数值来源，演示值标「合成」。
2. **出图。** 架构与 I/O 描述同一条流水线时，默认合画。以数据流为主线，在处理节点标注脚本名和职责，用独立线型表示函数提供关系，按 [HEP 分析流水线](references/hep-pipeline.md) 标注箭头。需要详述调用先后、返回或并行时，再补时序图。交付可编辑的 `.mmd` 或 Mermaid 代码块。
3. **预览。** 优先复用当前会话已验证的目标渲染器。渲染后核对箭头两端、分支汇合、边的遮挡和标签换行。Pele 扩展按目标渲染器选用。正式科研结果图用 `hep-scientific-plotting`。

图型参考：[Pele Examples](https://pele.run/examples) · [Mermaid 语法](https://mermaid.js.org/intro/syntax-reference.html)。
