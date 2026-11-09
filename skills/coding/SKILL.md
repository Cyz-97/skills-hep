---
name: coding
description: 编写或重构高能物理的面向流程 Python 分析脚本，适用于 PyROOT RDataFrame、DataFactory、ROOT 直方图及 notebook-style PART+cell 工作流，例如效率研究、本底对比和系统变异。
---

# 面向流程的 HEP 分析脚本

先读项目适用的 `AGENTS.md` 和相邻分析入口。沿用已有物理定义、分析 API 和环境；引入新依赖前询问用户。

需要用 Mermaid 说明现有或拟议架构、分析流程，或展示样本成分与资源开销时，转到 [diagram](../diagram/SKILL.md) 选图。

## 计算分工

- **Python** 负责配置、ROOT I/O、串接步骤、调用现有拟合或展开 API、处理汇总后的直方图、打印和绘图。可以按样本、通道或变异点组织流程。
- **PyROOT** 用 `RDataFrame.Define` 和 `Filter` 中的 C++ 表达式逐步做切选和派生计算。列名体现物理含义，逐事例或逐粒子的重计算在这层完成，尽量避免新建 C++ 动态库。确需在 Python 中执行这类循环时，说明具体卡点并先取得用户明确授权。
- **ROOT / DataFactory** 用 `Histo1D`、`Histo2D` 汇总，再用 `HistStaff` / `HistFactory` 表达结果。NumPy 用于结果 I/O 和绘图的转换，尽量避免 `AsNumpy` 拉出事件列。
- **批量读取** 按样本组织 ROOT 路径，优先复用项目的 `RDFFactory`。先看当前版本的入口契约；直接调用 `TChain.Add(value)` 的版本应传字符串路径或通配模式。运行参数优先放在脚本配置 cell 或现有环境变量中，避免新增 JSON 依赖和读取隐藏目录下的 JSON。
- **随机数** 优先使用 ROOT 自带的生成器。串行流程可直接用 `gRandom`（PyROOT 中为 `ROOT.gRandom`）；启用隐式多线程的 RDF 在 C++ 计算层使用每个处理 slot 独立的 ROOT 生成器（如 `TRandom3`，通过 `DefineSlot` 选取）。按用户明确约定实现固定种子或跨分片可复现性。参见 [ROOT 随机数](https://root.cern.ch/doc/master/classTRandom.html)与 [RDataFrame 多线程接口](https://root.cern.ch/doc/master/classROOT_1_1RDataFrame.html)。
- **哈希** 需要哈希校验时先询问用户采用什么方案，取得明确指示后再加入。

## Part 和 cell

1. 按配置与读取、派生变量和切选、统计与核对、展示划分 Part。每个 Part 放多个 cell。用以下标题标明阶段，并在标题下写清该阶段的物理口径。

   ```python
   # ----------------------------
   #       PART 1: Load the sample
   # ----------------------------
   # State the selection or assumptions for this stage.
   ```

2. 一个 cell 完成一个可命名的动作。编号在全文件连续递增，输入和输出写实际变量、图或诊断。变量和 import 尽量放在首次使用的 cell，共用配置放在首次需要它的配置 cell。

   ```python
   # %%
   # cell 1: Book the generated truth histogram.
   # input: Signal RDF before reconstructed selection.
   # output: truth_hist.
   ```

3. 在独立绘图 cell 中使用已算好的结果，调用 `plt.show()`，并按任务约定保存指定格式。不超过 200 行的绘图 cell 直接在 cell 内写绘图步骤；仅在用户明确要求时将其封装成函数。局部对齐连续赋值的 `=`、多行字典同层的 `:` 和相邻行尾的 `#`。为单位、分母和物理切选补充必要说明。
4. 同一份 `.py` 应支持直接执行和从干净内核按 cell 顺序运行。分析入口独立于 `test_*.py`。验证时用最小合成输入运行关键 RDF action，检查 C++ JIT、直方图结果及绘图入口，按实际执行范围报告。

需要起步模板时，参考 [两 Part、四 cell 的合成示例](assets/part-cell.py)。把其中的合成输入换成项目已有的样本入口。
