#!/usr/bin/env python3
"""渲染后几何检查 harness：非阻断地测量 DELPHI 标头、legend 与 data/MC 元素的 bbox。

工作原理：以受控环境重放绘图脚本（强制 Agg backend），包裹
``matplotlib.figure.Figure.savefig``，在每张 figure 首次保存前完成渲染测量。
测量内容与判定依据均来自绘图规范（SKILL.md / plotting-standard.md）的确定性配方：

- GEO001：figure 渲染结果中缺少 DELPHI 标头文字；
- GEO002：主图 axes 渲染宽高比偏离 4:3 超过容差；
- GEO003：DELPHI 标头与 data/MC 元素的渲染 bbox 重叠；
- GEO004：legend 与 data/MC 元素的渲染 bbox 重叠；
- GEO005：data/MC 内容侵入顶部 header band（配方要求内容压缩在图框下部 3/5）；
- GEO006：存在无法测量 bbox 的 data/MC artist，相关重叠检查被跳过；
- GEO007：脚本没有产生任何 savefig 调用，无法进行渲染几何检查；
- GEO000：脚本重放失败（语法、异常或非零退出）。

命令行仅在显式 --replay 时执行独立绘图脚本并重新保存产物；不重放分析脚本。
本工具不改源码，检查失败通过报告和退出码表达；bbox 重叠是候选问题，需视觉确认。
findings 作为工作流"修复迭代"步骤的输入，这是 harness 验证而非 validation 函数阻断。
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

TOP_FRACTION = 2.0 / 5.0            # header band 占主图图框高度的比例（规范硬门）
CONTENT_FRACTION = 1.0 - TOP_FRACTION  # 配方允许的内容上限：图框下部 3/5
BAND_INTRUSION_TOLERANCE = 0.02     # 内容超过 3/5 线 2% 高度以内视为测量噪声
ASPECT_TARGET = 4.0 / 3.0
ASPECT_TOLERANCE = 0.02             # 渲染宽高比相对 4:3 的相对偏差容差
OVERLAP_MIN_AREA = 1.0              # display px^2；小于该值的重叠视为测量噪声


@dataclass(frozen=True)
class GeometryFinding:
    """单条几何检查结论，分级与 lint_scientific_plots 保持一致。"""

    level: str
    code: str
    figure: str
    message: str

    def render(self, script: Path) -> str:
        return f"{self.level} [{self.code}] {script}:{self.figure} — {self.message}"


def _data_artists(ax) -> tuple[list, bool]:
    """收集主 axes 中代表 data/MC 内容的 artist，并标记是否存在二维 QuadMesh。"""
    artists: list = []
    has_quadmesh = False
    artists.extend(ax.lines)
    artists.extend(ax.patches)
    for collection in ax.collections:
        if type(collection).__name__ == "QuadMesh":
            has_quadmesh = True
        artists.append(collection)
    return artists, has_quadmesh


def _collection_points(artist) -> np.ndarray | None:
    """按集合类型提取数据坐标点：LineCollection 用 segments，其余用 offsets 或 paths。

    scatter 类集合的 paths 是围绕原点的单位 marker 形状，会污染 bbox，
    因此只取 offsets；fill_between 类 PolyCollection 则只有 paths 可用。
    """
    if hasattr(artist, "get_segments"):
        points: list = []
        for segment in artist.get_segments():
            points.extend(np.asarray(segment))
        if not points:
            return None
        return np.asarray(points, dtype=float)
    offsets = np.asarray(artist.get_offsets())
    if len(offsets):
        return offsets
    points = []
    for path in artist.get_paths():
        points.extend(path.vertices)
    if not points:
        return None
    return np.asarray(points, dtype=float)


def _artist_bbox(artist, renderer) -> Bbox | None:
    """测量 artist 的 display bbox；返回 None 表示该类型无法可靠测量。"""
    if type(artist).__name__ == "QuadMesh":
        # QuadMesh 没有稳定的 get_window_extent 实现，从数据坐标显式变换。
        coordinates = artist.get_coordinates().reshape(-1, 2)
        points = artist.axes.transData.transform(coordinates)
        return Bbox(np.column_stack([points.min(axis=0), points.max(axis=0)]))
    if isinstance(artist, matplotlib.collections.Collection):
        if artist.axes is None:
            return None
        points = _collection_points(artist)
        if points is None:
            return None
        display = artist.axes.transData.transform(points)
        return Bbox(np.column_stack([display.min(axis=0), display.max(axis=0)]))
    try:
        bbox = artist.get_window_extent(renderer)
    except (NotImplementedError, AttributeError, ValueError, TypeError):
        return None
    if bbox is None or not np.all(np.isfinite(bbox.extents)):
        return None
    return bbox


def _overlap_area(first: Bbox, second: Bbox) -> float:
    """两个 display bbox 的交集面积。"""
    x0 = max(first.x0, second.x0)
    y0 = max(first.y0, second.y0)
    x1 = min(first.x1, second.x1)
    y1 = min(first.y1, second.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def audit_figure(fig, figure_name: str) -> list[GeometryFinding]:
    """对单张已布局的 figure 做渲染测量并返回 findings。"""
    findings: list[GeometryFinding] = []

    def add(level: str, code: str, message: str) -> None:
        findings.append(GeometryFinding(level, code, figure_name, message))

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    if not fig.axes:
        add("错误", "GEO001", "figure 没有可检查的 axes")
        return findings

    # DELPHI 标头：mplhep.label.exp_label 以 Text/Annotation 形式挂在 axes 上。
    header_texts = [
        text for ax in fig.axes for text in ax.texts if "DELPHI" in text.get_text()
    ]
    if not header_texts:
        add("错误", "GEO001", "渲染结果中缺少 DELPHI 标头文字")

    # 主图 = 渲染高度最大的 axes；存在 ratio/residual 子图时仍会选中主面板。
    # 优先使用标头所属面板，避免把同高的 colorbar 选为主图。
    main_ax = header_texts[0].axes if header_texts else max(
        fig.axes, key=lambda ax: ax.get_window_extent(renderer).height
    )
    main_box = main_ax.get_window_extent(renderer)
    rendered_ratio = main_box.width / main_box.height
    data_artists, has_quadmesh = _data_artists(main_ax)
    equal_geometry = has_quadmesh and main_ax.get_aspect() == 1.0
    if not equal_geometry and abs(rendered_ratio - ASPECT_TARGET) / ASPECT_TARGET > ASPECT_TOLERANCE:
        add(
            "错误",
            "GEO002",
            f"主图渲染宽高比为 {rendered_ratio:.3f}，偏离 4:3 超过 {ASPECT_TOLERANCE:.0%}",
        )

    data_bboxes: list[Bbox] = []
    unmeasurable = 0
    for artist in data_artists:
        bbox = _artist_bbox(artist, renderer)
        if bbox is None:
            unmeasurable += 1
        else:
            data_bboxes.append(bbox)
    if unmeasurable:
        add(
            "警告",
            "GEO006",
            f"{unmeasurable} 个 data/MC artist 无法测量 bbox，涉及它们的重叠检查被跳过",
        )

    for text in header_texts:
        header_bbox = text.get_window_extent(renderer)
        if any(_overlap_area(header_bbox, bbox) > OVERLAP_MIN_AREA for bbox in data_bboxes):
            add("警告", "GEO003", "标头与 artist bbox 重叠；需视觉确认是否实际遮挡")
            break

    legend = main_ax.get_legend()
    if legend is not None:
        legend_bbox = legend.get_window_extent(renderer)
        if any(_overlap_area(legend_bbox, bbox) > OVERLAP_MIN_AREA for bbox in data_bboxes):
            add("警告", "GEO004", "legend 与 artist bbox 重叠；需视觉确认是否实际遮挡")

    # 顶部 band 侵入检查只适用于一维内容；二维 pcolormesh 按设计填满图框，
    # 其标头（loc=0）位于图框上沿之外，天然不构成侵入。
    if data_bboxes and not has_quadmesh:
        band_floor = main_box.y0 + CONTENT_FRACTION * main_box.height
        tolerance = BAND_INTRUSION_TOLERANCE * main_box.height
        data_top = max(bbox.y1 for bbox in data_bboxes)
        if data_top > band_floor + tolerance:
            add(
                "警告",
                "GEO005",
                "artist bbox 超过一维顶部留白边界；需视觉区分数据与参考线/区域标记",
            )
    return findings


def audit_script(script_path: Path) -> list[GeometryFinding]:
    """以受控环境重放脚本，包裹 savefig 并收集全部 figure 的几何 findings。"""
    from matplotlib.figure import Figure

    findings: list[GeometryFinding] = []
    audited: set[int] = set()
    original_savefig = Figure.savefig

    def savefig_wrapper(self, *args, **kwargs):
        key = id(self)
        if key not in audited:
            audited.add(key)
            findings.extend(audit_figure(self, f"figure{len(audited)}"))
        return original_savefig(self, *args, **kwargs)

    previous_cwd = Path.cwd()
    try:
        Figure.savefig = savefig_wrapper
        os.chdir(script_path.parent)
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:  # 脚本自身的退出码转化为报告，不中断 harness
        if exc.code not in (None, 0):
            findings.append(
                GeometryFinding("错误", "GEO000", "script", f"脚本以退出码 {exc.code} 终止")
            )
    except BaseException:  # harness 把脚本崩溃转化为报告；不能因脚本失败而失去测量结论
        findings.append(
            GeometryFinding(
                "错误",
                "GEO000",
                "script",
                "脚本重放失败：" + traceback.format_exc(limit=3).splitlines()[-1],
            )
        )
    finally:
        Figure.savefig = original_savefig
        os.chdir(previous_cwd)
        plt.close("all")

    if not audited and not any(finding.code == "GEO000" for finding in findings):
        findings.append(
            GeometryFinding(
                "警告",
                "GEO007",
                "script",
                "脚本没有产生 savefig 调用，无法进行渲染几何检查",
            )
        )
    return findings


def python_files(targets: list[Path]) -> list[Path]:
    """收集目标中的 Python 文件，跳过隐藏目录。"""
    files: set[Path] = set()
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            files.add(target)
        elif target.is_dir():
            for path in target.rglob("*.py"):
                if not any(part.startswith(".") for part in path.parts):
                    files.add(path)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染后几何检查（非阻断 harness）")
    parser.add_argument("targets", nargs="+", type=Path, help="绘图脚本或目录")
    parser.add_argument("--replay", action="store_true",
                        help="显式重放独立绘图脚本并保存产物；不得用于上游分析脚本")
    parser.add_argument("--json", type=Path, default=None, help="可选 JSON 报告输出路径")
    args = parser.parse_args()

    if not args.replay:
        print("未执行：脚本重放会重新运行并保存产物；仅对独立绘图脚本显式使用 --replay")
        return 1

    scripts = python_files(args.targets)
    if not scripts:
        print("错误 [GEO-CLI] 没有找到 Python 文件")
        return 1

    total_errors = 0
    total_warnings = 0
    report: dict = {"figures": []}
    for script in scripts:
        findings = audit_script(script)
        errors = sum(finding.level == "错误" for finding in findings)
        warnings = sum(finding.level == "警告" for finding in findings)
        total_errors += errors
        total_warnings += warnings
        print(f"=== {script} ===")
        for finding in findings:
            print(finding.render(script))
        print(
            f"完成：{script.name} 包含 {len(findings)} 条 findings"
            f"（{errors} 个错误，{warnings} 个警告）"
        )
        report["figures"].append(
            {"script": str(script), "findings": [asdict(finding) for finding in findings]}
        )

    print(
        f"几何检查完成：{len(scripts)} 个脚本，{total_errors} 个错误，{total_warnings} 个警告"
    )
    if args.json is not None:
        report["summary"] = {"错误": total_errors, "警告": total_warnings}
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"JSON 报告已写入 {args.json}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
