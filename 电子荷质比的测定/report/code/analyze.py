from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    data = json.loads(Path("measurements.json").read_text())
    coefficient = data["K_T_per_A"]
    reference = data["reference_C_per_kg"]
    formula = data["formula"]
    mirror = data["mirror"]
    graph = data["graph"]
    formula_radius = (
        formula["initial_diameter_mm"]
        + np.arange(len(formula["I_A"])) * formula["diameter_step_mm"]
    ) / 2
    mirror_radius = (np.array(mirror["Sn_mm"]) - mirror["S0_mm"]) / 2

    def ratios(voltage, currents, radii):
        return 2 * voltage / (coefficient * np.array(currents) * radii / 1000) ** 2

    formula_values = ratios(formula["U_V"], formula["I_A"], formula_radius)
    mirror_values = ratios(mirror["U_V"], mirror["I_A"], mirror_radius)
    squared = np.array(graph["I_A"]) ** 2
    voltage = np.array(graph["U_V"])
    slope, intercept = np.polyfit(squared, voltage, 1)
    predictions = slope * squared + intercept
    residual_sum = np.sum((voltage - predictions) ** 2)
    fit_quality = 1 - residual_sum / np.sum((voltage - voltage.mean()) ** 2)
    assumed_radius = graph["assumed_radius_mm"]
    graph_value = 2 * slope / (coefficient * assumed_radius / 1000) ** 2
    values = {
        "K": f"{coefficient * 1e4:.2f}",
        "Reference": f"{reference / 1e11:.3f}",
        "FormulaMean": f"{formula_values.mean() / 1e11:.3f}",
        "MirrorMean": f"{mirror_values.mean() / 1e11:.3f}",
        "FormulaError": f"{abs(formula_values.mean() / reference - 1) * 100:.2f}",
        "MirrorError": f"{abs(mirror_values.mean() / reference - 1) * 100:.2f}",
        "Slope": f"{slope:.3f}",
        "Intercept": f"{intercept:.3f}",
        "FitQuality": f"{fit_quality:.4f}",
        "AssumedRadius": f"{assumed_radius:g}",
        "GraphValue": f"{graph_value / 1e11:.3f}",
        "GraphError": f"{abs(graph_value / reference - 1) * 100:.2f}",
        "LastMirrorError": f"{abs(mirror_values[-1] / reference - 1) * 100:.1f}",
    }
    Path("values.tex").write_text(
        "\n".join(r"\newcommand{\V" + key + "}{" + value + "}" for key, value in values.items())
    )
    results = {
        "formula_radius_mm": formula_radius.tolist(),
        "formula_C_per_kg": formula_values.tolist(),
        "mirror_radius_mm": mirror_radius.tolist(),
        "mirror_C_per_kg": mirror_values.tolist(),
        "I_squared_A2": squared.tolist(),
        "slope_V_per_A2": float(slope),
        "intercept_V": float(intercept),
        "R_squared": float(fit_quality),
        "display": values,
    }
    Path("results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 10, "pdf.fonttype": 42})
    figure, axes = plt.subplots(figsize=(5.5, 2.5))
    axes.scatter(squared, voltage, color="black", s=22, label="Data", zorder=3)
    grid = np.linspace(squared.min() - 0.03, squared.max() + 0.03, 100)
    axes.plot(grid, slope * grid + intercept, color="#355c7d", linewidth=1.3, label="Fit")
    axes.set_xlabel(r"$I^2\ /\ \mathrm{A^2}$")
    axes.set_ylabel(r"$U\ /\ \mathrm{V}$")
    axes.legend(frameon=False)
    axes.spines[["top", "right"]].set_visible(False)
    figure.tight_layout(pad=0.5)
    figure.savefig("fit.pdf")
    plt.close(figure)

    markdown = Path("postlab.md").read_text()
    for key, value in values.items():
        markdown = markdown.replace("{{" + key + "}}", value)
    Path("rendered.md").write_text(markdown)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
