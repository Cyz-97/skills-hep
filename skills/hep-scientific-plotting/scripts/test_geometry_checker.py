#!/usr/bin/env python3
"""check_plot_geometry 的标准库单元测试；Agg 后端下直接测量构造的 figure。"""

from __future__ import annotations

import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import mplhep  # noqa: E402
import numpy as np  # noqa: E402

from check_plot_geometry import audit_figure  # noqa: E402


def build_compliant_figure():
    """构造直接使用标准绘图 API 的 Data/MC 图，比例不作为门槛。"""
    rng = np.random.default_rng(1994)
    edges = np.linspace(0.0, 10.0, 21)
    centers = 0.5 * (edges[:-1] + edges[1:])
    mc = 100.0 * np.exp(-centers / 6.0)
    mc_err = np.sqrt(mc)
    data = mc + rng.normal(0.0, np.sqrt(mc))
    data_err = np.sqrt(np.clip(data, 1.0, None))

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.stairs(mc, edges, color="C0", label=r"$\text{Simulation}$")
    ax.bar(
        centers, 2 * mc_err, width=np.diff(edges), bottom=mc - mc_err,
        fill=False, linewidth=0, edgecolor="C0", hatch="////", alpha=0.55,
    )
    ax.errorbar(centers, data, yerr=data_err, color="black", ls="none", marker="o")
    mplhep.label.exp_label(
        loc=1, exp="DELPHI", data=False, llabel="Open Data",
        italic=[False, True, False], fontsize=8, rlabel="1994", ax=ax,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98), frameon=False)
    return fig


class GeometryAuditTests(unittest.TestCase):
    def test_compliant_layout_has_no_errors(self):
        fig = build_compliant_figure()
        try:
            findings = audit_figure(fig, "good")
        finally:
            plt.close(fig)
        self.assertEqual([f for f in findings if f.level == "错误"], [])

    def test_possible_overlap_is_advisory(self):
        # 任意画布比例与正常留白均允许；只提示可能的实际遮挡。
        fig, ax = plt.subplots(figsize=(8, 5))
        edges = np.linspace(0.0, 1.0, 6)
        values = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        ax.stairs(values, edges, color="C0", label=r"$\text{Simulation}$")
        ax.legend(loc="upper left")
        try:
            findings = audit_figure(fig, "bad")
        finally:
            plt.close(fig)
        codes = {finding.code for finding in findings}
        self.assertIn("GEO004", codes)
        self.assertNotIn("GEO002", codes)
        self.assertNotIn("GEO005", codes)
        self.assertEqual([item for item in findings if item.level == "错误"], [])

    def test_cli_does_not_replay_without_explicit_flag(self):
        # 哨兵脚本若被运行会写文件；省略 --replay 必须保持输入目录不变。
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "executed.txt"
            script = root / "plot.py"
            script.write_text("from pathlib import Path\nPath('executed.txt').write_text('ran')\n")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("check_plot_geometry.py")), str(script)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("未执行", result.stdout)
            self.assertFalse(marker.exists())

    def test_equal_geometry_matrix_is_not_forced_to_four_by_three(self):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pcolormesh(np.arange(3), np.arange(3), np.ones((2, 2)))
        ax.set_aspect("equal")
        mplhep.label.exp_label(loc=0, exp="DELPHI", data=False, llabel="Simulation", ax=ax)
        try:
            findings = audit_figure(fig, "matrix")
        finally:
            plt.close(fig)
        self.assertNotIn("GEO002", {finding.code for finding in findings})

    def test_shared_axes_width_and_aspect_are_preserved(self):
        # 模拟 DataFactory 的共享 x 轴布局；检查不能强制锁定主图并压窄副图。
        fig, (ax, residual_ax) = plt.subplots(2, 1, sharex=True,
            figsize=(3.5, 3.5), gridspec_kw={"height_ratios": [4, 1]})
        ax.errorbar([1, 2], [3, 4], yerr=[0.1, 0.2])
        residual_ax.errorbar([1, 2], [0.1, -0.1], yerr=[0.1, 0.1])
        mplhep.label.exp_label(loc=1, exp="DELPHI", data=False, llabel="Open Data", ax=ax)
        try:
            findings = audit_figure(fig, "shared")
            widths = [panel.get_window_extent().width for panel in (ax, residual_ax)]
            self.assertAlmostEqual(widths[0], widths[1])
            self.assertIsNone(ax.get_box_aspect())
            self.assertIsNone(residual_ax.get_box_aspect())
            self.assertNotIn("GEO002", {item.code for item in findings})
        finally:
            plt.close(fig)

    def test_missing_header_reported(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot([0.0, 1.0], [0.0, 1.0])
        try:
            findings = audit_figure(fig, "noheader")
        finally:
            plt.close(fig)
        self.assertIn("GEO001", {finding.code for finding in findings})


if __name__ == "__main__":
    unittest.main()
