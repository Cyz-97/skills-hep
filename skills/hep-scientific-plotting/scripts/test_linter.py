#!/usr/bin/env python3
"""检查真实返工来源及科学风险；所有源码仅解析，不执行上游或保存图像。"""
import tempfile
import unittest
from pathlib import Path

from lint_scientific_plots import lint_file


class LinterTests(unittest.TestCase):
    def test_mixed_cells_wrapper_and_dynamic_caption_are_not_style_errors(self):
        source = '''
from datafactory.plot import compare_hist1d as draw
rdf = rdf.Define("observable", "x")
install_engineering_tick_formatting()
ax, ratio_ax = draw(data, mc, xlabel=label)
caption = f"{producer}: {observable}; weights={weights}"
ax.figure.savefig(output / f"{observable}.pdf", metadata={"Subject": caption})
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "analysis.py"
            path.write_text(source)
            findings = lint_file(path)
        self.assertEqual([item for item in findings if item.level == "错误"], [])
        self.assertEqual({item.code for item in findings}, {"SCI002"})

    def test_invalid_ratio_placeholder_remains_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot.py"
            path.write_text("ratio = np.divide(a, b, where=b != 0, out=np.ones_like(a))\n")
            findings = lint_file(path)
            self.assertIn("SCI001", {item.code for item in findings})
            path.write_text("ratio = np.divide(a, b, where=b != 0, out=np.full_like(a, np.nan))\n")
            self.assertEqual(lint_file(path), [])

    def test_uncertainty_kwargs_and_positional_arguments_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot.py"
            path.write_text("ax.errorbar(x, y, err)\nax.errorbar(x, y, **plot_kwargs)\n")
            self.assertEqual(lint_file(path), [])
            path.write_text("ax.errorbar(x, y)\n")
            self.assertEqual({item.code for item in lint_file(path)}, {"ERR001"})

    def test_negative_literal_error_and_syntax_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot.py"
            path.write_text("ax.errorbar(x, y, yerr=[[1, -2], [3, 4]])\n")
            self.assertEqual({item.code for item in lint_file(path)}, {"SCI003"})
            path.write_text("ax.errorbar(\n")
            self.assertEqual({item.code for item in lint_file(path)}, {"PY001"})

    def test_aesthetic_api_choices_do_not_trigger_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plot.py"
            path.write_text('''
fig, (ax, ratio_ax) = plt.subplots(2, 1, sharex=True)
ax.errorbar(x, y, yerr=errors, label="Data")
ax.grid(False)
fig.savefig(output_path, metadata={"Subject": caption})
''')
            self.assertEqual(lint_file(path), [])


if __name__ == "__main__":
    unittest.main()
