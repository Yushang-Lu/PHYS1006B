from pathlib import Path
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "phys1006b-mpl"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import numpy as np


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONT = Path(
    "/Users/jinana/Library/Containers/com.kingsoft.wpsoffice.mac/Data/"
    ".kingsoft/office6/data/fonts/online_ext_font_cache/HYShuSongErKW.ttf"
)


def main():
    measurements = json.loads((ASSETS / "measurements.json").read_text())
    frequency = np.asarray(measurements["frequency_1e14_Hz"])
    charge = measurements["elementary_charge_C"]
    reference = measurements["template_planck_reference_J_s"]
    low_indices = np.argsort(frequency)[:2]
    high_indices = np.argsort(frequency)[-2:]
    low_frequency = float(frequency[low_indices].mean())
    high_frequency = float(frequency[high_indices].mean())
    count = frequency.size
    results = []
    rows = []
    plt.rcParams.update(
        {
            "font.family": "STIXGeneral",
            "font.size": 9,
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.6,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    figure, axes = plt.subplots(1, 3, figsize=(5.768, 2.16), sharex=True, sharey=True)
    line_frequency = np.linspace(5.1, 8.3, 150)
    for axis, (diameter, raw_voltage) in zip(
        axes, measurements["signed_stopping_voltage_V"].items()
    ):
        voltage = -np.asarray(raw_voltage)
        assert count == voltage.size == 5
        assert np.all(voltage > 0)
        slope = float(
            (count * np.dot(frequency, voltage) - frequency.sum() * voltage.sum())
            / (count * np.dot(frequency, frequency) - frequency.sum() ** 2)
        )
        intercept = float(voltage.mean() - slope * frequency.mean())
        np.testing.assert_allclose(
            [slope, intercept], np.polyfit(frequency, voltage, 1), atol=1e-12
        )
        low_voltage = float(voltage[low_indices].mean())
        high_voltage = float(voltage[high_indices].mean())
        graphical_slope = (high_voltage - low_voltage) / (high_frequency - low_frequency)
        graphical_intercept = low_voltage - graphical_slope * low_frequency
        planck_ls = charge * slope * 1e-14
        planck_graph = charge * graphical_slope * 1e-14
        error_ls = abs(planck_ls / reference - 1) * 100
        error_graph = abs(planck_graph / reference - 1) * 100
        residuals = voltage - (slope * frequency + intercept)
        np.testing.assert_allclose(residuals.sum(), 0, atol=1e-12)
        results.append(
            {
                "diameter_mm": int(diameter),
                "least_squares": {
                    "slope_V_per_scaled_frequency": slope,
                    "intercept_V": intercept,
                    "planck_J_s": planck_ls,
                    "relative_error_percent": error_ls,
                    "residuals_V": residuals.tolist(),
                },
                "graphical_group_mean_line": {
                    "low_mean_point": [low_frequency, low_voltage],
                    "high_mean_point": [high_frequency, high_voltage],
                    "slope_V_per_scaled_frequency": graphical_slope,
                    "intercept_V": graphical_intercept,
                    "planck_J_s": planck_graph,
                    "relative_error_percent": error_graph,
                },
            }
        )
        rows.append(
            f"{diameter} & {slope:.5f} & {intercept:.5f} & "
            f"{planck_ls / 1e-34:.3f} & {error_ls:.2f} & "
            f"{planck_graph / 1e-34:.3f} & {error_graph:.2f}" + r" \\"
        )
        axis.plot(frequency, voltage, "o", color="#202020", ms=3, zorder=3)
        axis.plot(
            line_frequency, slope * line_frequency + intercept,
            color="#285b87", lw=1.05,
        )
        axis.plot(
            line_frequency, graphical_slope * line_frequency + graphical_intercept,
            color="#b36928", lw=1.0, ls=(0, (4, 2)),
        )
        axis.set_title(f"{diameter} mm", fontsize=9, pad=4)
        axis.set_xlim(5.0, 8.45)
        axis.set_ylim(0.4, 2.05)
        axis.set_xticks([5, 6, 7, 8])
        axis.set_yticks([0.5, 1.0, 1.5, 2.0])
        axis.grid(alpha=0.16, linewidth=0.4)
        axis.tick_params(labelsize=8, width=0.6, length=3)
        axis.set_xlabel(r"$\nu\ (10^{14}\,\mathrm{Hz})$", labelpad=2)
    axes[0].set_ylabel(r"$U_0\ (\mathrm{V})$", labelpad=3)
    figure.legend(
        handles=[
            Line2D([], [], color="#202020", marker="o", ls="", ms=3, label="测量值"),
            Line2D([], [], color="#285b87", lw=1.05, label="最小二乘"),
            Line2D([], [], color="#b36928", lw=1.0, ls="--", label="作图线"),
        ],
        loc="upper center", ncol=3, frameon=False,
        prop=FontProperties(fname=FONT, size=8.5),
        bbox_to_anchor=(0.53, 1.02), handlelength=2.0, columnspacing=2.0,
    )
    figure.subplots_adjust(left=0.085, right=0.993, bottom=0.23, top=0.75, wspace=0.12)
    figure.savefig(ASSETS / "stopping_voltage.pdf")
    figure.savefig(ASSETS / "stopping_voltage.png", dpi=240)
    plt.close(figure)
    (ASSETS / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    (ASSETS / "results_rows.tex").write_text(
        "\\newcommand{\\ResultsRows}{%\n" + "\n".join(rows) + "\n}\n"
    )
    for result in results:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
