# Mermaid 简要数据图

使用已知汇总值，注明样本、测量条件和单位。CPU 时间和磁盘占用通常分图。

| 目的 | 选图与口径 | 合成例图 |
|---|---|---|
| 样本成分 | `pie showData`：同一分母下互斥的正贡献；带符号贡献用条形图 | [成分](../assets/composition.mmd) |
| 比较不同步骤的耗时或磁盘量 | `xychart` + `bar`：统一输入规模和测量口径，注明 CPU time 或 wall time、独占或累计 | [CPU 耗时](../assets/cpu-time.mmd) |
| 看用量随数据量的趋势 | `xychart` + `line`：使用等间隔采样或明确标注有序类别；要保留不等间距时改用真实数值坐标的绘图库 | [磁盘占用](../assets/disk-scaling.mmd) |

目标渲染器缺少 XY chart 时，可交付数据表，或按需要用项目绘图工具出图。参见 [Mermaid Pie](https://mermaid.js.org/syntax/pie.html) 与 [Mermaid XY Chart](https://mermaid.js.org/syntax/xyChart.html)。
