import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def linear_fit(horizontal, vertical):
    slope = np.dot(horizontal - horizontal.mean(), vertical - vertical.mean())
    slope /= np.dot(horizontal - horizontal.mean(), horizontal - horizontal.mean())
    intercept = vertical.mean() - slope * horizontal.mean()
    independent = np.polyfit(horizontal, vertical, 1)
    np.testing.assert_allclose([slope, intercept], independent, rtol=1e-10, atol=1e-10)
    return float(slope), float(intercept)


def markdown_to_tex(markdown):
    output = []
    for block in markdown.strip().split("\n\n"):
        if block.startswith("### "):
            output.append(r"\subsection{" + block[4:] + "}")
        elif block.startswith("## "):
            output.append(r"\section{" + block[3:] + "}")
        elif block.startswith("$$\n"):
            output.append("\\[\n" + block[3:-3] + "\n\\]")
        elif block.startswith("!["):
            image = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", block)
            if image is None:
                raise ValueError(f"Unsupported image block: {block}")
            width = "0.94" if image[2] == "hall.pdf" else "0.80"
            output.append(
                "\\begin{center}\n"
                + rf"\includegraphics[width={width}\linewidth]{{{image[2]}}}"
                + "\n\\end{center}"
            )
        elif block.startswith("|"):
            rows = [line.strip("|").split("|") for line in block.splitlines()]
            output.append(r"\begin{center}\small\setlength{\tabcolsep}{5pt}")
            output.append(r"\begin{tabular}{" + "r" * len(rows[0]) + "}")
            output.append(r"\toprule")
            output.append(" & ".join(rows[0]) + r"\\ \midrule")
            output.extend(" & ".join(row) + r"\\" for row in rows[2:])
            output.append(r"\bottomrule\end{tabular}\end{center}")
        else:
            output.append(block)
    return "\n\n".join(output) + "\n"


def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / "measurements.json").read_text())
    constants = data["constants"]
    current = np.array(data["current_mA"], dtype=float)
    assert len(current) == 6 and np.all(np.diff(current) > 0)
    assert [series["temperature_C"] for series in data["series"]] == list(range(10, 61, 10))
    thickness = constants["thickness_mm"] * 1e-3
    charge = constants["charge_C"]
    results = []
    audit = []
    for series in data["series"]:
        voltage = np.array(series["voltages_mV"], dtype=float)
        assert voltage.shape == (6, 4) and np.all(np.isfinite(voltage))
        assert np.all(voltage[:, [0, 2]] > 0) and np.all(voltage[:, [1, 3]] < 0)
        hall = (voltage[:, 0] - voltage[:, 1] + voltage[:, 2] - voltage[:, 3]) / 4
        field = (series["B1_Gs"] - series["B2_Gs"]) * 1e-4 / 2
        assert field > 0
        slope, intercept = linear_fit(current, hall)
        coefficient = abs(slope) * thickness / field
        result = {
            "temperature_C": series["temperature_C"],
            "temperature_K": series["temperature_C"] + constants["kelvin_offset"],
            "B_T": field,
            "VH_mV": hall.tolist(),
            "slope_V_A": slope,
            "intercept_mV": intercept,
            "RH_m3_C": coefficient,
            "n_m3": 1 / (charge * coefficient),
            "KH_V_A_T": abs(slope) / field,
        }
        results.append(result)
        delta = hall - np.array(series["handwritten_VH_mV"])
        audit.append({
            "temperature_C": series["temperature_C"],
            "difference_recomputed_minus_handwritten_mV": delta.tolist(),
            "above_rounding_tolerance": np.flatnonzero(abs(delta) > 0.00501).tolist(),
        })
        np.testing.assert_allclose(
            hall * 1e-3,
            np.array(series["voltages_mV"]) @ np.array([1, -1, 1, -1]) * 1e-3 / 4,
        )

    inverse_temperature = 1 / np.array([row["temperature_K"] for row in results])
    log_coefficient = np.log([row["RH_m3_C"] for row in results])
    gap_slope, gap_intercept = linear_fit(inverse_temperature, log_coefficient)
    gap_joule = 2 * constants["boltzmann_J_K"] * gap_slope
    gap_ev = gap_joule / charge
    relative_difference = abs(gap_ev / constants["reference_gap_eV"] - 1) * 100
    summary = {
        "series": results,
        "gap_slope_K": gap_slope,
        "gap_intercept": gap_intercept,
        "gap_J": gap_joule,
        "gap_eV": gap_ev,
        "relative_difference_percent": relative_difference,
    }
    Path("results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    Path("transcription_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "mathtext.fontset": "stix",
        "axes.linewidth": 0.7,
    })
    figure, axes = plt.subplots(figsize=(6.5, 3.15), layout="constrained")
    grid = np.linspace(current.min(), current.max(), 100)
    colors = ["#183c68", "#236a8a", "#15958a", "#98a63b", "#cf903c", "#ab4b51"]
    for result, color, marker in zip(results, colors, ["o", "s", "^", "D", "v", "P"]):
        axes.plot(grid, result["slope_V_A"] * grid + result["intercept_mV"], color=color, lw=1)
        axes.scatter(current, result["VH_mV"], s=24, marker=marker, color=color,
                     label=f'{result["temperature_C"]} °C', zorder=3)
    axes.set(xlabel=r"$I_S$ (mA)", ylabel=r"$V_H$ (mV)", xticks=current)
    axes.legend(frameon=False, ncol=2, fontsize=9, loc="upper left")
    figure.savefig("hall.pdf")
    plt.close(figure)

    figure, axes = plt.subplots(figsize=(5.8, 2.7), layout="constrained")
    temperature_grid = np.linspace(inverse_temperature.min(), inverse_temperature.max(), 100)
    axes.plot(temperature_grid * 1e3, gap_slope * temperature_grid + gap_intercept,
              color="#183c68", lw=1.2, label="Fit")
    axes.scatter(inverse_temperature * 1e3, log_coefficient, color="#183c68", s=28,
                 label="Data", zorder=3)
    axes.set(xlabel=r"$1/T$ ($10^{-3}$ K$^{-1}$)",
             ylabel=r"$\ln[|R_H|/(\mathrm{m^3/C})]$")
    axes.legend(frameon=False, fontsize=9)
    figure.savefig("gap.pdf")
    plt.close(figure)

    table = [
        "| $t/{}^\\circ\\mathrm C$ | $B/\\mathrm{mT}$ | $a/(\\mathrm{V/A})$ | $c/\\mathrm{mV}$ | $\\lvert R_H\\rvert/(\\mathrm{m^3/C})$ | $n/(10^{18}\\,\\mathrm{m^{-3}})$ | $\\lvert K_H\\rvert/(\\mathrm{V/(A\\,T)})$ |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in results:
        table.append(
            f'| {row["temperature_C"]} | {row["B_T"] * 1e3:.2f} | '
            f'{row["slope_V_A"]:.3f} | {row["intercept_mV"]:.3f} | '
            f'{row["RH_m3_C"]:.4f} | {row["n_m3"] / 1e18:.4f} | {row["KH_V_A_T"]:.1f} |'
        )
    gap_result = (
        f"拟合得 $A={gap_slope:.2f}\\,\\mathrm K$，$C={gap_intercept:.5f}$，因此\n\n"
        "$$\n"
        f"E_g={gap_joule / 1e-20:.4f}\\times10^{{-20}}\\,\\mathrm J"
        f"={gap_ev:.4f}\\,\\mathrm{{eV}}.\n"
        "$$"
    )
    comparison = (
        f"禁带宽度测量值与指导书给出的常温参考值 "
        f"${constants['reference_gap_eV']:.2f}\\,\\mathrm{{eV}}$ "
        f"的相对偏差为 ${relative_difference:.1f}\\%$。"
    )
    markdown = (root / "report.md").read_text()
    markdown = markdown.replace("@@SUMMARY_TABLE@@", "\n".join(table))
    markdown = markdown.replace("@@GAP_RESULT@@", gap_result).replace("@@COMPARISON@@", comparison)
    assert "@@" not in markdown
    Path("analysis.md").write_text(markdown)
    Path("body.tex").write_text(markdown_to_tex(markdown))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Handwritten VH checks:", json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
