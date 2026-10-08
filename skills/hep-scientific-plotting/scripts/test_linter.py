#!/usr/bin/env python3
"""lint_scientific_plots 的标准库单元测试；fixtures 为自包含 inline 配方脚本。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lint_scientific_plots import lint_file


GOOD_SOURCE = r'''
import matplotlib.pyplot as plt
import mplhep
import numpy as np
from matplotlib.ticker import FuncFormatter

CAPTION = "选择后的动量分布及模拟统计误差带。误差带只包含模拟样本的统计误差。"

def main():
    edges = np.array([0.5, 1.5, 2.5])
    centers = 0.5 * (edges[:-1] + edges[1:])
    x = centers
    data = np.array([3.0, 4.0])
    data_err = np.array([0.2, 0.3])
    mc = np.array([2.8, 3.9])
    mc_err = np.array([0.1, 0.2])

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.stairs(mc, edges, color="C0", label=r"$\text{Simulation}$")
    ax.bar(centers, 2 * mc_err, width=np.diff(edges), bottom=mc - mc_err,
           fill=False, linewidth=0, edgecolor="C0", hatch="////", alpha=0.55,
           label=r"$\text{Simulation stat. unc.}$")
    n_points = len(x)
    if n_points > 80:
        capsize, markersize = 0.0, 1.6
    else:
        capsize, markersize = 3.0, 3.0
    ax.errorbar(x, data, yerr=data_err, color="black", ls="none", marker="o",
                markersize=markersize, elinewidth=0.8, capthick=0.64,
                capsize=capsize, label=r"$\text{Data}$")
    ax.set(xlabel=r"$x$", ylabel=r"$\text{Events / bin}$")
    exponent = 0
    fmt = lambda value, _: "0" if value == 0 else f"{value / 10**exponent:.6g}"
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.grid(False)
    ax.set_box_aspect(3 / 4)
    tops = [np.max(data + data_err), np.max(mc + mc_err)]
    lower, upper_now = ax.get_ylim()
    ax.set_ylim(lower, max(upper_now, lower + (max(tops) - lower) / 0.6))
    mplhep.label.exp_label(loc=1, exp="DELPHI", data=False, llabel="Open Data",
                           italic=[False, True, False], fontsize=8,
                           rlabel=r"1994, $\sqrt{s}=91.2\,\mathrm{GeV}$", ax=ax)
    ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98), frameon=False)
    fig.savefig("figures/momentum.pdf", bbox_inches="tight", dpi=300, transparent=True)
    plt.show()

if __name__ == "__main__":
    main()
'''


BAD_SOURCE = r'''
import matplotlib.pyplot as plt

def main():
    df = ROOT.RDataFrame("events", "input.root").Filter("x > 0")
    fig, ax = plt.subplots()
    ax.errorbar([1, 2], [3, 4])
    mesh = ax.pcolormesh([[1, 2], [3, 4]])
    plt.colorbar(mesh)
    ax.grid()
    fig.savefig("bad.png")
'''


class LinterTests(unittest.TestCase):
    def test_good_source_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_good.py"
            path.write_text(GOOD_SOURCE, encoding="utf-8")
            self.assertEqual(lint_file(path), [])

    def test_bad_source_reports_core_violations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_bad.py"
            path.write_text(BAD_SOURCE, encoding="utf-8")
            codes = {finding.code for finding in lint_file(path)}
            self.assertTrue(
                {"SEP001", "ERR001", "GRID001", "2D001", "LAB001", "CAP001", "OUT002"}
                <= codes
            )

    def test_project_configuration_is_outside_linter_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENT.md").write_text("datafactory_path: /missing/package\n")
            path = root / "plot.py"
            path.write_text(GOOD_SOURCE)
            self.assertEqual(lint_file(path), [])

    def test_tick_scientific_notation_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "plot_invalid_ticks.py"
            invalid.write_text(
                GOOD_SOURCE.replace(
                    "ax.grid(False)",
                    'ax.set_xticklabels([r"$\\times 10^{6} + 91$"])\n'
                    '    ax.set_yticklabels([r"$\\times 10^{4}$", "1000", "0.001"])\n'
                    "    ax.grid(False)",
                ),
                encoding="utf-8",
            )
            invalid_codes = {finding.code for finding in lint_file(invalid)}
            self.assertTrue({"TICK001", "TICK002", "TICK004"} <= invalid_codes)

            valid = Path(directory) / "plot_valid_ticks.py"
            valid.write_text(
                GOOD_SOURCE.replace(
                    "ax.grid(False)",
                    'ax.set_xticklabels([r"$\\times 10^{3}$"])\n'
                    '    ax.set_yticklabels([r"$\\times 10^{-3}$", "0", "0.01", "999"])\n'
                    "    ax.grid(False)",
                ),
                encoding="utf-8",
            )
            valid_codes = {finding.code for finding in lint_file(valid)}
            self.assertNotIn("TICK001", valid_codes)
            self.assertNotIn("TICK002", valid_codes)
            self.assertNotIn("TICK004", valid_codes)

    def test_engineering_formatter_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_missing_engineering_formatter.py"
            path.write_text(
                GOOD_SOURCE.replace(
                    "    exponent = 0\n"
                    "    fmt = lambda value, _: \"0\" if value == 0 "
                    "else f\"{value / 10**exponent:.6g}\"\n"
                    "    ax.yaxis.set_major_formatter(FuncFormatter(fmt))\n",
                    "",
                ),
                encoding="utf-8",
            )
            codes = {finding.code for finding in lint_file(path)}
            self.assertIn("TICK005", codes)

    def test_mixed_data_mc_rejects_simulation_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_wrong_mixed_header.py"
            path.write_text(
                GOOD_SOURCE.replace(
                    'llabel="Open Data"',
                    'llabel="Simulation Preliminary"',
                ),
                encoding="utf-8",
            )
            codes = {finding.code for finding in lint_file(path)}
            self.assertIn("LAB003", codes)

    def test_fit_curve_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "plot_invalid_fit.py"
            invalid.write_text(
                GOOD_SOURCE.replace(
                    "ax.grid(False)",
                    'ax.plot([0, 1], [1, 2], color="red", label="Signal")\n'
                    '    ax.plot([0, 1], [1, 2], color="red", label="Total fit")\n'
                    "    ax.grid(False)",
                ),
                encoding="utf-8",
            )
            invalid_codes = {finding.code for finding in lint_file(invalid)}
            self.assertTrue({"FIT001", "FIT002", "FIT003"} <= invalid_codes)

            valid = Path(directory) / "plot_valid_fit.py"
            valid.write_text(
                GOOD_SOURCE.replace(
                    "ax.grid(False)",
                    'ax.plot([0, 1], [2, 3], color="black", label="Total fit")\n'
                    '    ax.plot([0, 1], [1, 2], color="blue", label="Background")\n'
                    "    ax.grid(False)",
                ),
                encoding="utf-8",
            )
            valid_codes = {finding.code for finding in lint_file(valid)}
            self.assertNotIn("FIT001", valid_codes)
            self.assertNotIn("FIT002", valid_codes)
            self.assertNotIn("FIT003", valid_codes)

    def test_plain_label_gets_mathtext_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_plain_label.py"
            path.write_text(
                GOOD_SOURCE.replace(r'label=r"$\text{Data}$"', 'label="Data"'),
                encoding="utf-8",
            )
            codes = {finding.code for finding in lint_file(path)}
            self.assertIn("LBL001", codes)

    def test_layout_recipe_guards_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_missing_geometry.py"
            source = GOOD_SOURCE.replace(
                "    ax.set_box_aspect(3 / 4)\n", ""
            ).replace(
                "    ax.set_ylim(lower, max(upper_now, lower + (max(tops) - lower) / 0.6))\n",
                "",
            ).replace(
                'ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98), frameon=False)',
                "ax.legend()",
            )
            path.write_text(source, encoding="utf-8")
            codes = {finding.code for finding in lint_file(path)}
            self.assertTrue({"LAY002", "LAY003", "LAY004"} <= codes)

    def test_blocking_layout_validation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot_blocking_validation.py"
            path.write_text(
                GOOD_SOURCE.replace(
                    'ax.legend(loc="upper right", bbox_to_anchor=(0.98, 0.98), frameon=False)',
                    "validate_header_layout(ax, None, None)",
                ),
                encoding="utf-8",
            )
            codes = {finding.code for finding in lint_file(path)}
            self.assertIn("LAY005", codes)

    def test_multi_panel_requires_y_label_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "plot_multi_missing_alignment.py"
            missing.write_text(
                GOOD_SOURCE.replace(
                    "fig, ax = plt.subplots(figsize=(8, 6))",
                    "fig, (ax, ratio_ax) = plt.subplots(2, 1, figsize=(8, 8))",
                ),
                encoding="utf-8",
            )
            missing_codes = {finding.code for finding in lint_file(missing)}
            self.assertIn("LAY001", missing_codes)

            aligned = Path(directory) / "plot_multi_aligned.py"
            aligned.write_text(
                missing.read_text(encoding="utf-8").replace(
                    "ax.grid(False)",
                    "fig.align_ylabels((ax, ratio_ax))\n    ax.grid(False)",
                ),
                encoding="utf-8",
            )
            aligned_codes = {finding.code for finding in lint_file(aligned)}
            self.assertNotIn("LAY001", aligned_codes)


if __name__ == "__main__":
    unittest.main()
