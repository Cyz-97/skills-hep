#!/usr/bin/env python3
"""静态检查 HEP 科研绘图脚本，输出中文诊断。"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: Path
    line: int
    message: str

    def render(self) -> str:
        return f"{self.level} [{self.code}] {self.path}:{self.line} — {self.message}"


ANALYSIS_PATTERNS = {
    "RDataFrame": "绘图文件中出现 RDataFrame；请把事件处理移到上游分析代码",
    r"\.Filter\s*\(": "绘图文件中出现 Filter；请把事件选择移到上游",
    r"\.Define\s*\(": "绘图文件中出现 Define；请把变量定义移到上游",
    r"\bcurve_fit\s*\(": "绘图阶段出现拟合；请在上一个 cell 完成拟合，再从内存绘制结果",
    r"\bminimize\s*\(": "绘图文件中出现最小化；请把统计推断移到上游",
    r"\bunfold(?:ing)?\b": "绘图文件中出现 unfolding；请加载上游持久化结果",
    r"sideband.{0,30}(?:subtract|transfer|scale)": "绘图文件疑似推导 sideband 修正",
    r"systematic.{0,30}(?:combine|quadrature|covariance)": "绘图文件疑似组合系统学误差",
}

SCI_EXPONENT = re.compile(r"\\times\s*10\s*\^\s*\{?\s*([+-]?\d+)\s*\}?")
ADDITIVE_OFFSET = re.compile(
    r"\\times\s*10\s*\^\s*\{?\s*[+-]?\d+\s*\}?\s*[+−]\s*"
)
PLAIN_NUMERIC_LABEL = re.compile(
    r"^\s*\$?\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*\$?\s*$"
)


def line_of(text: str, match: re.Match[str] | None) -> int:
    if match is None:
        return 0
    return text.count("\n", 0, match.start()) + 1


def python_files(targets: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            files.add(target)
        elif target.is_dir():
            for path in target.rglob("*.py"):
                if not any(part.startswith(".") for part in path.parts):
                    files.add(path)
    return sorted(files)


def call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.expr = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def has_keyword(node: ast.Call, name: str) -> bool:
    return any(keyword.arg == name for keyword in node.keywords)


def looks_like_plot(text: str) -> bool:
    signals = (
        "savefig(",
        ".errorbar(",
        ".stairs(",
        ".pcolormesh(",
        "compare_mc_data(",
        "compare_hist1d(",
    )
    return any(signal in text for signal in signals)


def has_caption(path: Path, text: str) -> bool:
    if re.search(r"\bCAPTION\s*=", text):
        return True
    candidates = (
        path.with_suffix(".caption.md"),
        path.parent / "captions.md",
        path.parent / "figure_captions.md",
    )
    return any(candidate.exists() for candidate in candidates)


def string_literals(node: ast.AST) -> list[str]:
    """提取调用参数中的静态字符串，供 tick label 规则检查。"""
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def tick_label_strings(node: ast.Call, name: str) -> list[str]:
    """返回显式设置的 X/Y tick label 字符串。"""
    if name.endswith("set_xticklabels") or name.endswith("set_yticklabels"):
        return string_literals(node)
    if name.endswith("set_xticks") or name.endswith("set_yticks"):
        for keyword in node.keywords:
            if keyword.arg == "labels":
                return string_literals(keyword.value)
    return []


def numeric_constants(node: ast.AST) -> list[float]:
    """提取数值常量，排除 bool。"""
    return [
        float(child.value)
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, (int, float))
        and not isinstance(child.value, bool)
    ]


def tick_label_numbers(node: ast.Call, name: str) -> list[float]:
    """返回显式设置的 Y tick label 数值。"""
    label_node: ast.AST | None = None
    if name.endswith("set_yticklabels") and node.args:
        label_node = node.args[0]
    elif name.endswith("set_yticks"):
        label_node = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "labels"),
            None,
        )
    if label_node is None:
        return []

    values = numeric_constants(label_node)
    for label in string_literals(label_node):
        match = PLAIN_NUMERIC_LABEL.fullmatch(label)
        if match:
            values.append(float(match.group(1)))
    return values


def keyword_string(node: ast.Call, name: str) -> str | None:
    """返回调用中指定关键字的静态字符串值。"""
    for keyword in node.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def is_mathtext_string(value: str) -> bool:
    """判断静态标签是否置于完整的 mathtext ``$...$`` 环境。"""
    stripped = value.strip()
    return len(stripped) >= 2 and stripped.startswith("$") and stripped.endswith("$")


def keyword_token(node: ast.Call, name: str) -> str | None:
    """返回关键字的静态字符串或变量名，供颜色规则使用。"""
    for keyword in node.keywords:
        if keyword.arg != name:
            continue
        if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value.lower()
        if isinstance(keyword.value, ast.Name):
            return keyword.value.id.lower()
    return None


def lint_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if not looks_like_plot(text):
        return findings

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [
            Finding("错误", "PY001", path, exc.lineno or 0, f"Python 语法错误：{exc.msg}")
        ]

    datafactory_mode = bool(
        re.search(r"(?:from|import)\s+datafactory", text)
        or re.search(r"\bcompare_(?:mc_data|hist1d|hist1d_multi2one)\s*\(", text)
    )

    for pattern, message in ANALYSIS_PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            findings.append(
                Finding("错误", "SEP001", path, line_of(text, match), message)
            )

    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    call_names = [call_name(node) for node in calls]
    fit_trigger = bool(
        re.search(r"\b(?:total\s+fit|background|fit[_ ]?result)\b", text, re.IGNORECASE)
    )
    plot_label_strings: list[tuple[ast.Call, str]] = []

    for node, name in zip(calls, call_names):
        label_values: list[str] = []
        for keyword in node.keywords:
            if keyword.arg in {"label", "xlabel", "ylabel"}:
                if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, str
                ):
                    label_values.append(keyword.value.value)
        if name.endswith("set_xlabel") or name.endswith("set_ylabel"):
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                label_values.append(node.args[0].value)
        for label_value in label_values:
            if not is_mathtext_string(label_value):
                findings.append(
                    Finding(
                        "警告",
                        "LBL001",
                        path,
                        node.lineno,
                        "label、legend 文字或坐标轴 label 建议使用完整的 $...$ mathtext 环境",
                    )
                )
        if name.endswith("plot"):
            label = keyword_string(node, "label")
            if label is not None:
                plot_label_strings.append((node, label))
        if name.endswith("errorbar") and not has_keyword(node, "yerr"):
            findings.append(
                Finding(
                    "错误",
                    "ERR001",
                    path,
                    node.lineno,
                    "errorbar 缺少显式 yerr",
                )
            )
        if name.endswith("grid"):
            enabled = not node.args and not node.keywords
            if node.args and isinstance(node.args[0], ast.Constant):
                enabled = node.args[0].value is not False
            if enabled:
                findings.append(
                    Finding(
                        "错误",
                        "GRID001",
                        path,
                        node.lineno,
                        "默认不得开启 ax.grid；请删除调用或显式使用 grid(False)",
                    )
                )
        if name in {"plt.colorbar", "pyplot.colorbar"}:
            findings.append(
                Finding(
                    "错误",
                    "2D001",
                    path,
                    node.lineno,
                    "二维图必须使用独立 colorbar axes，禁止 plt.colorbar",
                )
            )
        if name.endswith("colorbar") and has_keyword(node, "ax"):
            findings.append(
                Finding(
                    "错误",
                    "2D002",
                    path,
                    node.lineno,
                    "colorbar 不得通过 ax= 挤压主图；请传入独立 cax",
                )
            )

        for label in tick_label_strings(node, name):
            offset = ADDITIVE_OFFSET.search(label)
            if offset:
                findings.append(
                    Finding(
                        "错误",
                        "TICK001",
                        path,
                        node.lineno,
                        "X/Y tick label 禁止使用 '\\times 10^{n} + m' 加性 offset",
                    )
                )
            for match in SCI_EXPONENT.finditer(label):
                exponent = int(match.group(1))
                if exponent % 3 != 0:
                    findings.append(
                        Finding(
                            "错误",
                            "TICK002",
                            path,
                            node.lineno,
                            "进位单位指数必须是 3 的倍数",
                        )
                    )
        for value in tick_label_numbers(node, name):
            magnitude = abs(value)
            if magnitude > 999.0 or 0.0 < magnitude < 0.01:
                findings.append(
                    Finding(
                        "错误",
                        "TICK004",
                        path,
                        node.lineno,
                        "Y tick label 的有限非零绝对值必须位于 [0.01, 999]",
                    )
                )

    offset_setting = re.search(
        r"(?:useOffset\s*=\s*True|set_useOffset\s*\(\s*True\s*\))", text
    )
    if offset_setting:
        findings.append(
            Finding(
                "错误",
                "TICK003",
                path,
                line_of(text, offset_setting),
                "X/Y 轴不得开启 Matplotlib 加性 offset；请使用 useOffset=False",
            )
        )

    has_engineering_formatter = (
        "set_major_formatter" in text
        or "set_offset_text" in text
        or "EngineeringScalarFormatter" in text
        or re.search(r"set_(?:x|y)scale\s*\(\s*[\"']log[\"']", text) is not None
    )
    if not has_engineering_formatter:
        findings.append(
            Finding(
                "错误",
                "TICK005",
                path,
                0,
                "Y 轴必须应用 3 的倍数工程进位格式（规范第 11 节的 inline 配方或 log scale）",
            )
        )

    if fit_trigger:
        has_black_total = any(
            re.search(r"(?:total\s+fit|overall|整体)", label, re.IGNORECASE)
            and keyword_token(node, "color") in {"black", "k"}
            for node, label in plot_label_strings
        )
        has_blue_background = any(
            re.search(r"(?:background|本底)", label, re.IGNORECASE)
            and keyword_token(node, "color") in {"blue", "b"}
            for node, label in plot_label_strings
        )
        if not has_black_total:
            findings.append(
                Finding("错误", "FIT001", path, 0, "拟合图缺少黑色整体拟合曲线")
            )
        if not has_blue_background:
            findings.append(
                Finding("错误", "FIT002", path, 0, "拟合图缺少蓝色本底曲线")
            )
    for node, label in plot_label_strings:
        if re.search(r"(?:signal|sig(?:nal)?|信号)", label, re.IGNORECASE):
            findings.append(
                Finding(
                    "错误",
                    "FIT003",
                    path,
                    node.lineno,
                    "拟合图不得显示独立信号成分曲线",
                )
            )

    if re.search(r"\.(?:imshow|hist2d)\s*\(", text):
        match = re.search(r"\.(?:imshow|hist2d)\s*\(", text)
        findings.append(
            Finding(
                "错误",
                "2D003",
                path,
                line_of(text, match),
                "二维图必须使用 pcolormesh",
            )
        )

    has_pcolormesh = any(name.endswith("pcolormesh") for name in call_names)
    if has_pcolormesh and not (
        "make_axes_locatable" in text and "append_axes" in text
    ):
        findings.append(
            Finding(
                "错误",
                "2D004",
                path,
                0,
                "pcolormesh 缺少独立 cax 比例设置",
            )
        )
    if has_pcolormesh and not (".set_aspect(" in text):
        findings.append(
            Finding("警告", "2D005", path, 0, "请明确二维主 axes 的 aspect")
        )

    # mplhep.label.exp_label 是 DELPHI 标头的标准调用；旧版 bundled helper
    # add_delphi_label 仍被接受，以兼容历史绘图脚本。
    has_delphi_label_call = any(
        name.endswith(("add_delphi_label", "exp_label")) for name in call_names
    )
    if not has_delphi_label_call and not (
        "DELPHI Open Data" in text or "DELPHI Simulation" in text
    ):
        findings.append(
            Finding(
                "错误",
                "LAB001",
                path,
                0,
                "缺少 DELPHI Open Data 或 DELPHI Simulation 标头",
            )
        )

    if not has_delphi_label_call and not (
        re.search(r"fontfamily\s*=\s*[\"']sans-serif[\"']", text)
        and re.search(r"fontweight\s*=\s*[\"']bold[\"']", text)
    ):
        findings.append(
            Finding(
                "错误",
                "LAB002",
                path,
                0,
                "DELPHI 标头字样必须显式使用 sans-serif 粗体，建议调用 mplhep.label.exp_label",
            )
        )

    data_tokens_for_header = bool(
        re.search(r"\b(?:Open Data|Data)\b", text)
        or any(name.endswith("errorbar") for name in call_names)
    )
    mc_tokens_for_header = bool(
        re.search(r"\b(?:MC|Simulation)\b", text)
        or any(name.endswith("stairs") for name in call_names)
    )
    if data_tokens_for_header and mc_tokens_for_header:
        for node, name in zip(calls, call_names):
            if name.endswith("add_delphi_label"):
                uses_simulation = keyword_string(node, "kind") == "simulation"
            elif name.endswith("exp_label"):
                llabel_value = keyword_string(node, "llabel")
                uses_simulation = (
                    llabel_value is not None and "Simulation" in llabel_value
                )
            else:
                continue
            if uses_simulation:
                findings.append(
                    Finding(
                        "错误",
                        "LAB003",
                        path,
                        node.lineno,
                        "Data/MC 混合图的 DELPHI 标头必须使用 Open Data",
                    )
                )

    if not has_pcolormesh and not bool(
        re.search(
            r"\.set_box_aspect\s*\(\s*(?:0?\.75|3(?:\.0)?\s*/\s*4(?:\.0)?)\s*\)",
            text,
        )
    ):
        findings.append(
            Finding(
                "错误",
                "LAY002",
                path,
                0,
                "主图 axes 的物理宽高比必须固定为 4:3；有下方子图时也必须保持",
            )
        )
    # 顶部 header band 由确定性配方建立（一维图用 ylim 内容包络压缩，二维图用
    # subplots_adjust）；渲染后的实际占用由 harness 的 check_plot_geometry.py 测量。
    if not has_pcolormesh and not any(
        name.endswith("set_ylim") for name in call_names
    ) and "subplots_adjust" not in text:
        findings.append(
            Finding(
                "错误",
                "LAY003",
                path,
                0,
                "缺少顶部 header band 的确定性预留（ylim 内容包络压缩或 2D subplots_adjust）",
            )
        )
    legend_calls = [
        node for node, name in zip(calls, call_names) if name.endswith("legend")
    ]
    if legend_calls and not any(
        has_keyword(node, "bbox_to_anchor") for node in legend_calls
    ):
        findings.append(
            Finding(
                "警告",
                "LAY004",
                path,
                0,
                "legend 未用 bbox_to_anchor 锚定顶部右侧保护区；渲染结果由 check_plot_geometry.py 验证",
            )
        )
    # 绘图脚本内禁止阻断式布局校验；检验职责归属 harness（GEO 检查 + 视觉抽查）。
    blocking_validation = [
        node for node, name in zip(calls, call_names) if "validate" in name.lower()
    ]
    if blocking_validation:
        findings.append(
            Finding(
                "错误",
                "LAY005",
                path,
                blocking_validation[0].lineno,
                "绘图脚本内禁止阻断式布局校验（validate_*）；检验由 harness 的 check_plot_geometry.py 与视觉抽查完成",
            )
        )

    save_calls = [node for node, name in zip(calls, call_names) if name.endswith("savefig")]
    if save_calls:
        if ".pdf" not in text:
            findings.append(Finding("错误", "OUT001", path, 0, "缺少 PDF 输出"))
        if any(".png" in (ast.get_source_segment(text, node) or "") for node in save_calls):
            findings.append(Finding("错误", "OUT002", path, 0, "绘图只保存 PDF，不应保存 PNG"))
        if 'bbox_inches="tight"' not in text and "bbox_inches='tight'" not in text:
            findings.append(
                Finding("错误", "OUT003", path, 0, "savefig 缺少 bbox_inches='tight'")
            )
        if not any(
            name in {"plt.show", "pyplot.show", "plt.close", "pyplot.close"}
            for name in call_names
        ):
            findings.append(
                Finding(
                    "警告",
                    "OUT004",
                    path,
                    0,
                    "保存后应在交互式环境调用 plt.show()；无头批处理流程应关闭 figure",
                )
            )

    data_tokens = bool(re.search(r"[\"'](?:Data|Open Data)[\"']", text))
    mc_tokens = bool(re.search(r"[\"'](?:MC|Simulation)", text))
    if data_tokens and not any(name.endswith("errorbar") for name in call_names):
        findings.append(Finding("错误", "SEM001", path, 0, "Data 必须使用 errorbar"))
    if mc_tokens and not datafactory_mode:
        if not any(name.endswith("stairs") for name in call_names):
            findings.append(Finding("错误", "SEM002", path, 0, "MC 中心值必须使用 stairs"))
        if not ("hatch=" in text or "hatch =" in text):
            findings.append(
                Finding("错误", "SEM003", path, 0, "MC 误差必须使用 hatched bar")
            )

    if any(name.endswith("errorbar") for name in call_names) and not datafactory_mode:
        inline_adaptive = "> 80" in text and "capsize" in text and "markersize" in text
        if not inline_adaptive:
            findings.append(
                Finding(
                    "警告",
                    "ERR002",
                    path,
                    0,
                    "未检测到按 80 点阈值调整 cap 和 marker 的逻辑",
                )
            )

    multi_panel_subplots = any(
        name.endswith("subplots")
        and (
            any(
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, int)
                and argument.value > 1
                for argument in node.args[:2]
            )
            or any(
                keyword.arg in {"nrows", "ncols"}
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, int)
                and keyword.value.value > 1
                for keyword in node.keywords
            )
        )
        for node, name in zip(calls, call_names)
    )
    if multi_panel_subplots and not (
        "align_ylabels" in text
    ):
        findings.append(
            Finding(
                "警告",
                "LAY001",
                path,
                0,
                "多面板图应在保存前对齐同一列主图和子图的 y axis label",
            )
        )

    if not has_caption(path, text):
        findings.append(
            Finding(
                "错误",
                "CAP001",
                path,
                0,
                "缺少 CAPTION 常量或配套 caption Markdown 文件",
            )
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="静态检查 HEP 科研绘图脚本")
    parser.add_argument("targets", nargs="+", type=Path, help="Python 文件或目录")
    args = parser.parse_args()

    files = python_files(args.targets)
    if not files:
        print("错误 [CLI001] 没有找到 Python 文件")
        return 1

    findings: list[Finding] = []
    checked = 0
    for path in files:
        file_findings = lint_file(path)
        if looks_like_plot(path.read_text(encoding="utf-8", errors="replace")):
            checked += 1
        findings.extend(file_findings)

    for finding in findings:
        print(finding.render())

    errors = sum(finding.level == "错误" for finding in findings)
    warnings = sum(finding.level == "警告" for finding in findings)
    print(f"完成：检查 {checked} 个绘图文件，{errors} 个错误，{warnings} 个警告")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
