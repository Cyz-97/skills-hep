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
    """按规范确定性配方构造的一维 Data/MC 图：4:3、band 预留、mplhep 标头。"""
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
    ax.set_box_aspect(3 / 4)
    content_top = float(np.max(data + data_err))
    lower, upper = ax.get_ylim()
    ax.set_ylim(lower, max(upper, lower + (content_top - lower) / 0.6))
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

    def test_violations_are_reported(self):
        # 8x5 画布默认 axes 比例偏离 4:3；legend 压在左上数据区；内容占满图框。
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
        self.assertTrue({"GEO002", "GEO004", "GEO005"} <= codes)

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

    def test_missing_header_reported(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot([0.0, 1.0], [0.0, 1.0])
        ax.set_box_aspect(3 / 4)
        try:
            findings = audit_figure(fig, "noheader")
        finally:
            plt.close(fig)
        self.assertIn("GEO001", {finding.code for finding in findings})


if __name__ == "__main__":
    unittest.main()
