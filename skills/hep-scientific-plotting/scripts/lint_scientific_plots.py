#!/usr/bin/env python3
"""可选的科学表达静态提示；不执行源码、不检查布局或固定绘图 API。

静态代码无法证明归一化、有效 bin 或封装运行结果正确。本工具只报告
具体可疑模式：缺少可见误差参数、负的字面量误差、零分母占位比值。
提示需结合实际数据与渲染确认；语法或读取失败通过非零退出码报告。
用法：python lint_scientific_plots.py analysis.py（兼容 notebook-style 混合源码）。
"""
from __future__ import annotations

import argparse
import ast
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


def python_files(targets: list[Path]) -> list[Path]:
    """仅收集指定源码，目录模式跳过隐藏目录、缓存及绘图产物目录。"""
    files: set[Path] = set()
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            files.add(target)
        elif target.is_dir():
            for path in target.rglob("*.py"):
                if not any(part.startswith(".") or part in {"__pycache__", "node_modules", "plots"}
                           for part in path.relative_to(target).parts):
                    files.add(path)
    return sorted(files)


def lint_file(path: Path) -> list[Finding]:
    """分析显式调用；unknown/封装参数不推断为缺失，不读取或执行外部库。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [Finding("错误", "IO001", path, 0, f"源码无法读取：{exc}")]
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [Finding("错误", "PY001", path, exc.lineno or 0, f"Python 语法错误：{exc.msg}")]

    # 公共封装别名仍可能继承零分母占位语义；只给核对提示，不把调用本身判为错误。
    ratio_wrappers = {"compare_hist1d", "compare_hist1d_multi2one", "compare_mc_data"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("datafactory"):
            for imported in node.names:
                if imported.name in ratio_wrappers:
                    ratio_wrappers.add(imported.asname or imported.name)

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else (
            node.func.id if isinstance(node.func, ast.Name) else "")
        keywords = {item.arg: item.value for item in node.keywords if item.arg is not None}
        if name in ratio_wrappers:
            findings.append(Finding("提示", "SCI002", path, node.lineno,
                "复用 ratio 封装：确认零分母/无效 bin 没有作为值 1 的测量点；已有图保持现状时说明限制。"))
        if name == "divide" and "where" in keywords and "out" in keywords:
            output = keywords["out"]
            output_name = output.func.attr if isinstance(output, ast.Call) and isinstance(
                output.func, ast.Attribute) else (output.func.id if isinstance(output, ast.Call)
                and isinstance(output.func, ast.Name) else "")
            if output_name in {"ones", "ones_like"}:
                findings.append(Finding("提示", "SCI001", path, node.lineno,
                    "条件除法以 1 填充无效位置：核对这些 bin 已被 mask/明确标记，不能以占位值推断一致性。"))
        if name != "errorbar":
            continue
        yerr = keywords.get("yerr", node.args[2] if len(node.args) > 2 else None)
        expanded_kwargs = any(item.arg is None for item in node.keywords)
        if (yerr is None and not expanded_kwargs) or isinstance(yerr, ast.Constant) and yerr.value is None:
            findings.append(Finding("提示", "ERR001", path, node.lineno,
                "此 errorbar 未提供可见 yerr：确认误差已在其他 artist 表达，或输入是否缺少必要误差。"))
        if yerr is not None:
            # 仅识别字面量数组；不猜测变量、函数、NumPy 表达式或 **kwargs 的数值。
            try:
                literal = ast.literal_eval(yerr)
            except (ValueError, TypeError):
                continue
            pending = [literal]
            negative = False
            while pending:
                value = pending.pop()
                if isinstance(value, (list, tuple)):
                    pending.extend(value)
                elif isinstance(value, (int, float)) and value < 0:
                    negative = True
            if negative:
                findings.append(Finding("错误", "SCI003", path, node.lineno,
                    "显式 yerr 中有负误差长度；误差长度应非负，请核对上游区间与显示变换。"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="可选科学表达提示（不检查美学、不执行源码）")
    parser.add_argument("targets", nargs="+", type=Path, help="Python 文件或限定目录")
    args = parser.parse_args()
    files = python_files(args.targets)
    if not files:
        print("错误 [CLI001] 没有找到 Python 源码；未执行检查")
        return 1
    findings = [finding for path in files for finding in lint_file(path)]
    for finding in findings:
        print(finding.render())
    errors = sum(item.level == "错误" for item in findings)
    print(f"完成：检查 {len(files)} 个源码，{errors} 个错误，{len(findings) - errors} 个核对提示。")
    print("未检查实际数据或图像；没有提示不等于科学验证通过，无需为提示清零而重写布局。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
