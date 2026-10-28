# 科研绘图：科学表达与首次布局

## 目录

1. 适用范围
2. 输入与显示变换
3. DataFactory 封装
4. Data/MC 与拟合表达
5. DELPHI 标头
6. 一维示例
7. marker/cap 建议
8. 误差、归一化与无效 bin
9. Ratio、Residual 与 Pull
10. 二维图与 colorbar
11. 文字、单位和范围
12. 主副面板协调
13. PDF 输出
14. Caption
15. 异常形态
16. 概念图

## 1. 适用范围

任务边界与结束条件见 [SKILL.md](../SKILL.md)。科学含义必须正确；美学以协调、可读为目标，以下布局和配色是首次生成的建议。已可读的图不因美学偏差反复修改，用户要求保持现状时尊重其要求。

## 2. 输入与显示变换

使用当前图所需的中心值、binning、误差来源、样本身份与既定归一化。上游选择、拟合与统计估计可以在同文件的其他 cell 中；绘图 cell 只消费结果。缺少必要信息时报告缺项，不自行补造误差或物理定义。

单位或 bin-width 变换对值和误差同时应用。mask 标明原因与范围；真实负值与大误差保留，不用隐藏它们改善外观。

## 3. DataFactory 封装

复用项目提供的公开接口与样式，保留权重和误差语义。封装中的 errorbar、stairs、formatter 和元数据都可以满足要求，源码无需重复这些调用。仅为具体缺陷通过公开参数或返回的 axes 补充显示；不复制或修改库实现。

对 ratio 额外确认封装的零分母行为：某些封装以 1 填充无效比值，这不是测量结果；见第 8 节。已批准保留的图只记录限制，不为检查器重画。

## 4. Data/MC 与拟合表达

- Data 用 errorbar 展示最终值和误差；MC 用 stairs 展示中心值、无外边框的 hatched bar 展示不确定度，hatch 密度统一设置为 `hatch="//////////"`（10 个斜杠），包括 ratio 面板中的 MC 相对误差带。图例明确样本身份，避免“MC Data”。
- 优先黑色 Data 与 tab10 前三色 MC，分量多时辅以线型或 hatch；使用既有可读配色也可。
- 拟合使用上游提供的总曲线与本底曲线及其有效范围，默认总曲线黑色、本底蓝色，不额外显示信号曲线；不重新拟合或擅自外推。
- 参数面板使用项目精度规则，显示参数、误差和 $\chi^2/\mathrm{ndf}$；SymbolFit 模型的已有公式可在 caption 说明。拟合副面板定义见第 9 节。

## 5. DELPHI 标头

数据图的已知实验身份使用 `mplhep.label.exp_label`，混合 Data/MC 用 Open Data，纯模拟用 Simulation。示例：

```python
mplhep.label.exp_label(loc=1, exp="DELPHI", data=False, llabel="Open Data",
                      italic=[False, True, False], fontsize=8,
                      rlabel=r"1994, $\sqrt{s}=91.2\,\mathrm{GeV}$", ax=ax)
```

年份和能量仅使用已知信息，缺失项省略。一维标头通常在左上方、二维在图框外；给标头与 legend 留够空间即可，不设固定顶部保护区比例或坐标门槛。保留已可读的标头位置，不要求替换等价实现。

## 6. 一维示例

若没有复用封装，直接消费上游数组：

```python
centers = 0.5 * (edges[:-1] + edges[1:])
widths = np.diff(edges)
ax.stairs(mc, edges, color="C0", label="MC")
ax.bar(centers, 2 * mc_err, width=widths, bottom=mc - mc_err,
       fill=False, linewidth=0, edgecolor="C0", hatch="//////////")
ax.errorbar(centers, data, yerr=data_err, color="black",
            ls="", marker="o", label="Data")
```

可调整层次让数据点与误差可见。科学定义见第 8 节，面板协调见第 12 节。

## 7. marker/cap 建议

沿用项目或封装设置；自行绘图时，可用 80 点作为疏密参考：多点用 `markersize=1.6` 且不加 cap，少点用 `markersize=3`，`capthick` 约为误差线宽的 0.8 倍，全 cap 长度约为平均屏幕点间距的 0.2 倍。

`capsize` 是半 cap 的 point 长度；动态计算需在布局后将屏幕像素乘 `72/fig.dpi` 转成 point。单点无法估计间距，使用项目值或不加 cap。已有封装结果可读时，无需为了精确长度改写它。

## 8. 误差、归一化与无效 bin

作图前确认最终值是计数、密度、效率还是修正谱，权重是否已包含，以及比较是绝对尺度还是形状。不擅自重新归一化或二次加权。weighted MC 使用上游 Sumw2 误差；非对称误差保留上下区间，派生量不由中心值补造误差。

ratio 的 numerator-only 点误差和独立 denominator 相对误差带应明确拆分，同一来源只包含一次。分母误差带使用同一 bin edges，以 1 为中心的 hatch bars 表达，hatch 样式沿用第 4 节；若采用完整 ratio 误差，caption 说明独立带的作用，避免重复计入。

零分母、非有限值或上游标记无效的 bin 不提供测量 ratio；显示为缺失并在 caption/报告说明，必要时以明显符号标记无效区。占位值 1 不能用来说明一致性，也不能仅因没有报错就认为有效。统计诊断与图的有效 bin 范围应一致；发现不一致交回上游核对。

若用户要求已有图保持现状，将已知无效 bin 限制写入交付结论，明确不能用这些点推断一致性；不把此类受限结果描述为无问题。

## 9. Ratio、Residual 与 Pull

- 分布比较采用明确的 ratio 定义和 y=1 参考线；拟合 residual 为 `data/model - 1`，参考线 y=0。pull 仅展示上游提供的定义和误差。
- 拟合 residual 范围关于 0 对称、位于 $(-5,5)$，y ticks 不超过 6 个；越界信息明确标记，不隐藏真实偏差。
- 轴标签、caption 解释副面板语义和误差带；上下等宽与标签协调见第 12 节。

## 10. 二维图与 colorbar

优先 pcolormesh 和独立 colorbar axes，准备好边距使 colorbar 不压缩主面板或遮挡标签；已有等价、可读的方式也可沿用。

需要保持真实数据几何（相关矩阵、等比例物理坐标）时可用 `ax.set_aspect("equal")`，它是数据坐标比例，不是锁定上下子图大小的工具。其他二维图用 auto aspect，不为画布形状改变物理范围或 binning。

相关系数色标以零为中心、范围 `[-1,1]`；协方差用其实际单位与范围。负值分布采用能区分正负的色标。log 色标仅适用于合适的正值范围，零值和负值的处理需说明。

## 11. 文字、单位和范围

轴标签用物理名称与单位，数学变量和单位用 mathtext；纯文字可用自然文本。默认无 title/subtitle/suptitle、无坐标网格，信息放入标头、legend 或 caption。

范围覆盖有效值与误差；非负直方图优先零下限，减除或修正谱保留负值并适当显示零参考线。跨度大的正值图可用 log，含非正值时不强制 log。

优先工程计数法、无加性 offset，进位指数取 3 的倍数；项目有明确格式要求时遵循项目。无需为了 tick 数值区间或 formatter/API 写法持续调整已可读的图。

## 12. 主副面板协调

首次运行前用 figsize、GridSpec height_ratios 和边距准备布局。主图大致接近 4:3，上下主副面板等宽且共享 x 轴；副面板高度以看清 residual 为准，可直接沿用 DataFactory 布局。

用 `fig.align_ylabels((main_ax, sub_ax))` 或封装已有的等价方式协调 y labels；只显示必要的共享刻度。给标头、legend、参数面板留适当空间，排版目标尺寸下文字清晰，无关键遮挡即可。

不要求通过 `set_aspect`、`set_box_aspect` 锁定主副面板或达到精确比例；这些设置可能令共享 x 轴的实际绘图区宽度不一致。科学结果和可读性已满足时，不再为留白比例、面板高度或字体偏好追加迭代。

## 13. PDF 输出

默认只交付 PDF；Subject 使用动态 caption 变量、拼接字符串或封装提供的内容均可：

```python
fig.savefig(output_path, bbox_inches="tight", metadata={"Subject": caption})
plt.show()  # 交互式；无头运行用 plt.close(fig)
```

Subject 写明图意和来源；Notebook 使用已知 notebook 路径/cell 标识。命名和目录沿用项目约定，不同语义的产物应可区分。裁切后确认标签完整，不要求唯一的 savefig 参数组合。

## 14. Caption

自包含说明物理量、样本、选择阶段、归一化、各面板与误差来源；拟合说明有效区间，ratio 说明误差分量和无效 bin，已有重要限制应指出。通常两至四句，不机械重复颜色，不编造结论。

## 15. 异常形态

标记可疑大误差、系统学变化或异常相同的分布，说明观察和影响，将统计来源与输入核对事项交回上游。不重做统计估计，也不通过裁剪改善视觉一致性。

## 16. 概念图

使用已有明确分析关系绘制文字、箭头与 patches，确认关系和箭头含义正确、文字可读。尺寸随内容调整，不套用数据图的实验标头、比例、marker/cap 和误差要求；仍提供 PDF 和自包含 caption。
