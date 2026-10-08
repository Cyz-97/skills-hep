# 高能物理科研绘图规范

## 目录

1. 适用范围与优先级
2. 绘图输入与显示变换
3. DataFactory 集成
4. 图形语义和颜色
5. DELPHI 标头
6. 一维 Data/MC 图
7. 自适应数据误差棒
8. 派生量与误差传播
9. Ratio、Residual 和 Pull
10. 二维图与 colorbar
11. 坐标轴、图例和文字
12. 多面板、尺寸与报告排版
13. 文件输出与可复现性
14. Caption 与交叉引用
15. 专用物理图
16. 概念图

## 1. 适用范围与优先级

任务边界、优先级、工作流程与交付状态见 [SKILL.md](../SKILL.md)。本文件是数据表达、布局和输出规则的权威定义，按图类型读取对应章节。

## 2. 绘图输入与显示变换

当前图所需的输入包括 bin edges/坐标、中心值、误差及来源、数据/模拟身份、既定归一化和已知实验元数据。仅要求当前图实际使用的字段；非对称误差及有效 bin 信息原样保留。

绘图 cell/代码段消费最终结果。事件选择、拟合、权重推导、本底减除、效率修正和系统学估计在上游 cell/代码段完成；二者可位于同一 notebook-style 文件。绘图中的输入问题以醒目说明记录，缺少科学上必需的信息时按正文的状态约定跳过当前图。

允许的显示变换包括 bin center/width、单位转换、既定归一化、标记无效 bin 和屏幕坐标 capsize。DataFactory 可按已明确的语义从最终 histogram 生成显示用 ratio。mask 的范围及理由应说明，不能通过删除真实负值或大误差改善观感。

## 3. DataFactory 集成

使用项目提供的公开接口；按所需功能查询其公开 API，而不在 skill 中缓存默认画布、布局或实现细节。保留既有权重与误差语义，在返回的 figure/axes 上补充本文件要求的表达和输出。接口不足时补充标准 Matplotlib/mplhep 渲染；不复制或修改 DataFactory 实现。

## 4. 图形语义和颜色

### 数据与 MC

- Data 必须用 `Axes.errorbar` 表示中心值与误差。
- MC 中心值必须用 `Axes.stairs`。
- MC 不确定度必须用围绕中心值的 hatched bar；设置 `linewidth=0` 取消外边框，保留 hatch 所需的颜色。合并显示 MC unc 和 MC 的 legend，显示为带hatch的实线。
- 堆叠 MC 可用 `Axes.bar(..., bottom=...)`，保持 DataFactory 的分量顺序和权重。
- 总 MC 可额外用黑色 `stairs`；不得把总 MC 曲线标成某个单独 signal 分量。
- 拟合图在数据点和 MC 表达之外，叠加两条光滑曲线：整体拟合结果（黑色）和本底（蓝色）。不显示 Signal 成分曲线。
- 拟合模型仅在上游提供的有效区间绘制；不擅自外推。数据可覆盖更广范围，caption 说明拟合范围。
- 使用上游提供的参数、误差和 $\chi^2/\mathrm{ndf}$ 制作参数面板；residual 为 `data/model - 1`，y 范围关于 0 对称且在 $(-5,5)$ 内，y ticks 不超过 6 个。
- 每张拟合图仅包含一项拟合结果，多项拟合结果分别绘制。
- 上游提供整体与本底曲线的密集 `x_grid` 和对应 `y` 值（内存对象或既有缓存）；绘图脚本不得重新执行 fit、最小化或曲线参数推导。
- 整体与本底曲线用标准 `ax.plot` 绘制：

  ```python
  ax.plot(x_grid, total, color="black", linewidth=1.2, label=r"$\text{Total fit}$", zorder=20)
  ax.plot(x_grid, background, color="blue", linewidth=1.2, label=r"$\text{Background}$", zorder=19)
  ```

- caption 按第 14 节说明拟合与误差定义；参数面板遵循项目精度规范。
- 如果拟合模型使用 SymbolFit，则应该在 caption 中标记化简后的拟合公式。

### 颜色顺序

优先使用 Matplotlib `tab10`：

```python
tab10 = plt.get_cmap("tab10").colors
blue, orange, green = tab10[:3]
black = "black"
```

- 当图中只有一组 Data 和 MC 数据集时，优先使用黑色 markercolor 和 linecolor。
- 推荐映射：Data=黑色；总 MC=黑色；前三个主要 MC 分量=蓝、橙、绿。需要更多类别时继续使用 `tab10`，同时用线型、hatch 或 marker 增强区分。避免仅依赖红绿差异传递关键信息。
- 如果图中没有黑色样本，则将颜色顺序改为黑色 + `tab10`序列，总是以黑色优先。

## 5. DELPHI 标头与顶部保护区

DELPHI 标头（DELPHI label）是主面板左上角的两行实验身份信息，通过 `mplhep.label.exp_label` 添加。每张数据或模拟图必须显示该标头：

- 身份行由 `exp` 与 `llabel` 组成：`llabel` 只能取 `Open Data` 或 `Simulation`。图中只要包含 Data，包括同时显示 Data 与 MC 的图，就使用 `Open Data`；只有模拟时使用 `Simulation`。
- `exp="DELPHI"` 由 mplhep 渲染为无衬线黑体加粗。禁止用继承 Computer Modern/serif 的普通 mathtext `\mathbf{DELPHI}` 代替。`data=False` 与 `italic=[False, True, False]` 固定不变。
- 元数据放 `rlabel`，依次为使用的数据年份与质心系能量；缺失项直接省略，禁止推测。全部缺失时保持空串。
- `loc` 按图的维度选择：二维图用 `loc=0`，标头整体绘制在图框上沿之外；一维图用 `loc=1`，身份行内嵌在图框内左上角，`rlabel` 位于其正下方。

推荐调用：

```python
import mplhep

mplhep.label.exp_label(loc=1, exp="DELPHI", data=False, llabel="Open Data",
                       italic=[False, True, False], fontsize=8,
                       rlabel=r"1994, $\sqrt{s}=91.2\,\mathrm{GeV}$", ax=ax)
```

一维主图 axes 顶部 `2/5` 定义为 header band，由确定性配方建立：把全部内容包络（中心值加上侧误差）压缩到图框下部 `3/5`。header band 的左 `1/3` 与右 `1/3` 定义为保护区：

- 左保护区坐标范围为 axes fraction `x∈[0,1/3]`、`y∈[0.6,1]`，一维图只放 DELPHI 标头；
- 右保护区坐标范围为 `x∈[2/3,1]`、`y∈[0.6,1]`，只放 legend；
- 两个保护区中禁止出现 data/MC marker、errorbar、stairs、histogram fill、uncertainty band、fit/theory curve；
- 通过扩展 y range、调整主 axes 内的数据占用或其他不改变物理值的布局方法建立空白，禁止删除、移动或修改物理数据点来制造空白；
- label 与 legend 都必须完整落在各自保护区内。内容过多时缩短 legend 文案、增加列数、减小相对字号或扩大整张 figure 的绝对尺寸，同时维持第 12 节的主图比例。

顶部预留的 inline 配方（一维图；`series` 覆盖图中全部 data/MC 序列，`yerr` 可为对称 `(N,)` 或非对称 `(2, N)`，log 轴需先做变换再比较）：

```python
tops = []
for x_arr, y_arr, yerr_arr in series:
    upper = np.asarray(y_arr, dtype=float)
    if yerr_arr is not None:
        err = np.asarray(yerr_arr, dtype=float)
        upper = upper + (err if err.ndim == 1 else err[1])   # (2, N) 取上行误差
    finite = np.isfinite(upper)
    tops.append(np.max(upper[finite]))
lower, upper_now = ax.get_ylim()
ax.set_ylim(lower, max(upper_now, lower + (max(tops) - lower) / 0.6))
```

legend 的右上保护区锚定：

```python
ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98),
          bbox_transform=ax.transAxes, borderaxespad=0.0, frameon=False,
          fontsize="x-small")
```

线性轴可使用上述配方；对数轴应在 log 显示坐标中留白，不能直接套用线性公式。二维图使用图外标头。布局完成后按正文的检查流程确认实际渲染。副面板不重复 DELPHI 标头。

## 6. 一维 Data/MC 图

推荐层次从后到前为：堆叠 MC、MC 总误差带、总 MC stairs、Data errorbar、标签与图例。

```python
# MC 中心值
ax.stairs(mc, edges, color=blue, label=r"$\text{Simulation}$")

# 无外边框的 hatched MC 误差范围
centers = 0.5 * (edges[:-1] + edges[1:])
widths = np.diff(edges)
ax.bar(
    centers,
    2 * mc_err,
    width=widths,
    bottom=mc - mc_err,
    align="center",
    fill=False,
    linewidth=0,
    edgecolor=blue,
    hatch="////",
    alpha=0.55,
    label=r"$\text{Simulation stat. unc.}$",
)

# Data
ax.errorbar(
    centers,
    data,
    yerr=data_err,
    color="black",
    ls="",
    marker="o",
    label=r"$\text{Data}$",
)
```

保持 bin 边界一致。按 bin width 或总面积归一化时，对中心值和误差应用同一变换，并在 y 轴与 caption 中说明归一化。

误差来源及变换见第 8 节。绘图阶段消费上游给出的误差，而不从中心值补算。

## 7. 自适应数据误差棒

遵循项目 marker/cap 要求；无另行要求时，有效点数超过 80 使用 `markersize=1.6`、`capsize=0`；否则 `markersize=3`，`capthick=0.8*elinewidth`，全 cap 长度约为平均屏幕点间距的 `0.2` 倍。

`capsize` 是半个 cap 的长度，单位 point。因此在最终布局下，将 x 坐标经 `ax.transData` 转为屏幕坐标，平均间距乘 `72/fig.dpi` 后再乘 `0.1`。只统计实际绘制的有限点；少于两个点时无法估算间距，使用项目给定值或不加 cap。先定轴范围并 draw，再求屏幕间距。

直接调用 DataFactory 时通过公开参数调整。

## 8. 派生量与误差传播

未调用 DataFactory 绘图函数时，以下量必须显式提供 `yerr`：

- 归一化分布；
- 效率；
- 比值；
- 修正因子；
- EEC、event shape 或其他从计数计算的量；
- 系统学 shift；
- unfolding 或拟合结果。

### 上游误差的展示

上游提供误差及来源，绘图阶段只做既定显示变换，并对中心值与误差应用相同单位或 bin-width 变换。加权 MC 使用上游 sumw2，派生量不得从 bin content 补造误差。保留非对称区间、有效 bin 与已提供的相关性说明，不由绘图重新计算协方差或效率区间。

ratio 点若仅含分子贡献，独立分母误差带以 1 为中心展示分母相对误差；caption 明确拆分方式。复用 DataFactory 时核对既有语义，不重复传播同一来源。缺少科学上必需的误差时交回上游，跳过该图并记录未完成。

## 9. Ratio、Residual 和 Pull

- 分布比较使用既定 ratio；拟合比较按项目要求使用 residual。pull 仅在上游提供其定义和误差时展示，不以每个 bin 是否对应拟合参数作为适用条件。
- 副面板几何、共享坐标和标签对齐见第 12 节。
- Ratio 使用 `y=1` 参考线；residual 或 pull 使用 `y=0` 参考线。
- Ratio 的 y 范围根据数据确定；固定范围时用箭头标明越界点。
- 围绕 1 的独立分母误差带使用与主图分母/MC 误差相同的无边框 hatch bars；bar 的左右边界必须直接使用同一组 bin edges，不能用中心点连线或 `fill_between` 替代。实现与第 6 节的 hatched bar 片段相同：`bottom = 1 - relative_denominator_err`、高度 `2 * relative_denominator_err`（这里是分母的相对误差）。
- 当坐标轴和 caption 已表达 ratio 和误差带含义时，副面板省略重复文字。误差含义见第 8 节；可疑形态按第 15 节标记。
- 副面板 y ticks 保持稀疏，通常不超过 3–4 个。
- 主图下边界 tick 与副图上边界 tick 不得碰撞。
- 如同时显示 ratio 和 difference，明确各面板误差定义。

## 10. 二维图与 colorbar

二维数据必须使用 `pcolormesh`。colorbar 使用独立 axes，避免压缩主图：

```python
from mpl_toolkits.axes_grid1 import make_axes_locatable

mesh = ax.pcolormesh(x_edges, y_edges, values, shading="auto")
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="4%", pad=0.08)
cbar = fig.colorbar(mesh, cax=cax)
```

比例规则：

- 需要保持数据几何（例如相关矩阵或等比例物理坐标）时，优先于固定图框比例使用 `ax.set_aspect("equal")`，保证数据坐标中的 bin 几何比例正确。
- 其他二维图使用 `aspect="auto"` 和 `ax.set_box_aspect(3 / 4)`。不修改数据范围或 binning 来同时满足不相容的比例要求。
- colorbar 与主 axes 等高；不得直接 `plt.colorbar()` 或通过 `fig.colorbar(..., ax=ax)` 挤压主图。
- 相关矩阵使用以 0 为中心的发散色图，`vmin=-1, vmax=1`；协方差使用其实际单位和范围，不套用相关系数范围。
- 小于约 `10×10` 的矩阵可标数值；大矩阵保持清晰刻度和 colorbar。
- 对数色标必须处理零值、负值和 mask，并在 caption 说明。

## 11. 坐标轴、图例和文字

- 坐标轴使用可发表的物理名称，禁止泄漏 Python 变量名和未转义下划线。
- 有量纲的轴必须给出单位，例如 `$p \mathrm{\,[GeV]}$`。
- y 轴若包含 bin-width 归一化，使用易读的圆整 bin width；复杂可变 binning 直接写 `Events / bin` 并在 caption 说明。
- 非负分布跨度较大时可用 log scale；含负值的减除谱保持可见负值及误差，不强制 log。
- 坐标范围覆盖有效中心值和误差；减除与修正谱保留负值并适当显示零参考线。通常非负的直方图优先零下限；log y 下限依据最小正值设置。
- 避免裸 `1e6` offset；用下面的 inline 配方生成 3 的倍数工程进位单位：

  ```python
  fig.canvas.draw()  # 先完成布局，ticks 才是最终值
  ticks = np.asarray(ax.get_yticks(), dtype=float)
  values = np.abs(ticks[np.isfinite(ticks) & (ticks != 0)])
  logs = np.log10(values)
  # 选最接近 0、且使非零 tick 的 |v/10^n| 位于 [0.01, 999] 的 3 的倍数指数 n
  lo = int(np.ceil((logs.max() - np.log10(999.0)) / 3))
  hi = int(np.floor((logs.min() - np.log10(0.01)) / 3))
  if lo > hi:  # 单一指数无解：保留当前 formatter，并提示人工调整显示方案
      print("WARNING: 工程进位指数无解；请改用 log scale、调整单位或拆分面板")
  else:
      n = min(range(3 * lo, 3 * hi + 1, 3), key=abs)
      ax.yaxis.set_major_formatter(FuncFormatter(
          lambda value, _: "0" if value == 0 else f"{value / 10**n:.6g}"))
      if n:
          ax.text(0, 1.01, rf"$\times 10^{{{n}}}$", transform=ax.transAxes, va="bottom")
  ```
- 坐标轴 label、图例 label 和 legend 文字优先放在 `$...$` 环境；文字用 `\text{...}`，变量/单位用 `\mathrm{...}`。若 ratio 的语义已由轴标签和 caption 清楚表达，可以省略面板内重复文字。
- X、Y 轴 tick label 禁止使用 `\times 10^{n} + m`，包括 Matplotlib 自动生成的加性 offset。关闭 offset，例如 `ScalarFormatter(useOffset=False)` 或 `ax.ticklabel_format(useOffset=False)`。
- 需要进位单位时仅使用 `$\times 10^{n}$`。`n` 必须为 3 的倍数，所以 `\times 10^{3}`、`\times 10^{-3}`、`\times 10^{6}` 均合法，非 3 倍数指数不合法。指数为 0 时直接显示 tick 数字，省略 `$\times 10^{0}$`。
- Y 轴有限非零 tick label 的绝对值必须位于 `[0.01, 999]`；0 可正常显示。对原始 tick 整体除以 `10^n`，并选取最接近 0 且满足范围的 3 倍数指数。
- 一组 y ticks 跨度过大，导致任意单一工程指数都无法同时满足 `0.01` 下界和 `999` 上界时，使用 log scale、调整物理单位或拆分面板，并在 caption 中说明。
- 默认不调用 `ax.grid()`；若上游开启网格，显式 `ax.grid(False)`。
- 数据图标头和 legend 放置遵循第 5 节。
- 普通数据图不使用 axes title；信息放进 DELPHI 标头、图例标题或 caption。
- 文字、注释和越界箭头可以使用 DataFactory 的 `ax.text`/`annotate`，保持字号和线宽一致。
- 每张独立 axes 都要有必要标签；ratio、residual、pull 只保留所属副面板标签。


## 12. 多面板、尺寸与报告排版

一维数据图主 axes 固定 `4:3`，用 `ax.set_box_aspect(3 / 4)`。二维数据图比例见第 10 节，概念图见第 16 节。

- 下方副面板默认为主图高度的 `1/2`，用户或项目要求优先；增加 figure 总高度容纳它，保持主图比例。
- 主副面板等宽、`sharex=True`，共享一个 xlabel；legend 只放主面板，副面板 ylabel 用数学定义。
- 设置全部标签并完成布局后，在保存前 `fig.align_ylabels((main_ax, sub_ax))`；不以不同 labelpad 或硬编码坐标替代对齐。
- 面板间距适量，边界 ticks 不碰撞，共享坐标只显示必要 tick labels；colorbar 不压缩主图。
- 字体在报告目标尺寸下可读，多面板大小与边距协调。变量巡检可用 subplot grid；坐标网格仍按第 11 节。
- 物理上紧密耦合的 main+ratio、fit+residual 保持在同一 figure。

论文中组合彼此独立的图时，可在 LaTeX 中按统一高度排列。混合 1D 与 2D 面板时分别调整高度，让实际绘图区视觉等大。caption 用 left/right/top-left 等位置描述面板。

## 13. 文件输出与可复现性

每张交付图只保存 PDF：

```python
meta = {"Subject": f"{CAPTION}（源码：{Path(__file__).resolve()}）"}
fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight", dpi=300,
            transparent=True, metadata=meta)
plt.show()  # 保存后交互式显示；明确的无头批处理流程可改为 plt.close(fig)
```

示例的 Subject 包含第 14 节的 caption 与源码来源。Notebook 没有 `__file__` 时使用已知 notebook 路径或 cell 标识；输出目录和命名沿用项目约定，语义不同的产物应可区分。

## 14. Caption 与交叉引用

每张论文图必须有 2–4 句自包含 caption，依次说明：

1. 画了什么 observable、数据集和选择阶段；
2. 各面板、归一化、拟合或不确定度带的定义；
3. 图中看不到但解释结果必需的条件；
4. 读者应得到的主要观察或结论。

Caption 不机械重复颜色和图例。派生量、ratio 和拟合图必须说明误差来源、是否包含系统学、分母误差带包含哪些分量。复合图用统一 caption 综合各面板。

Pandoc 文档使用：

```markdown
![自包含 caption](figures/name.pdf){#fig:name}
```

正文用 `@fig:name` 引用；表格用 `@tbl:name`；公式用 `@eq:name`。

## 15. 专用物理图

### 系统学图与异常形态

标记超过常规显示范围的系统学变化、异常误差带或看起来完全相同的独立分布，说明观察到的现象和对图的解释影响。将低统计、误差来源、variation 匹配或输入来源的核对事项交给上游；本 skill 不重做统计估计或事件分析。上游已提供解释时引用该解释，不通过裁剪隐藏异常。

输入为空的请求图按正文标记缺输入，记录原因；不交付白图或占位图。

## 16. 概念图

用户要求流程、样本组成、修正链或区域定义图时，用已明确的分析关系绘制 patches、arrows 和文字。内容缺失时请求相关定义，不自行推导新的分析方案。

尺寸随内容调整，不要求 DELPHI 标头、数据图比例、marker/cap 或误差面板。仍采用第 11 节中适用的文字规则，以及第 13–14 节的 PDF 和自包含 caption。视觉检查以关系正确、箭头含义明确、文字可读为完成标准。
