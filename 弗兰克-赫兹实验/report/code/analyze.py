import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator


def main():
    data = json.loads(Path("measurements.json").read_text())
    series_results = []
    raw_rows = []
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "mathtext.fontset": "stix",
        "font.size": 9, "axes.labelsize": 10, "legend.fontsize": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42,
    })
    figure, axes = plt.subplots(1, 2, figsize=(6.1, 2.15))
    colors = ["#285b89", "#b35432"]
    for series_index, series in enumerate(data["series"]):
        voltages, currents = [], []
        for block in series["blocks"]:
            expected = round((block["end"] - block["start"]) / data["step"]) + 1
            if len(block["current"]) != expected:
                raise ValueError(f"数据段长度不符：{series['retarding_voltage']}, {block['start']}")
            voltages.extend(block["start"] + np.arange(expected) * data["step"])
            currents.extend(block["current"])
        voltages, currents = np.array(voltages), np.array(currents)
        if not np.array_equal(voltages, np.arange(181) * 0.5):
            raise ValueError("每组必须为0到90 V的181个连续采样点")
        for voltage, current in zip(voltages, currents):
            raw_rows.append([series["retarding_voltage"], voltage, current])
        peaks, local_fits = [], []
        for lower, upper in series["peak_search_windows"]:
            candidates = np.flatnonzero((voltages >= lower) & (voltages <= upper))
            center = int(candidates[np.argmax(currents[candidates])])
            indices = np.arange(center - 2, center + 3)
            relative_voltage = voltages[indices] - voltages[center]
            coefficients = np.polyfit(relative_voltage, currents[indices], 2)
            quadratic, linear, constant = coefficients
            peak = float(voltages[center] - linear / (2 * quadratic))
            if quadratic >= 0 or not voltages[indices[0]] < peak < voltages[indices[-1]]:
                raise ValueError("拟合极大值不在窗口内部")
            peaks.append(peak)
            local_fits.append({
                "sample_voltages": voltages[indices].tolist(),
                "sample_currents": currents[indices].tolist(),
                "origin_voltage": float(voltages[center]),
                "coefficients": coefficients.tolist(),
                "peak_voltage": peak,
                "peak_current": float(constant - linear ** 2 / (4 * quadratic)),
            })
        peaks = np.array(peaks)
        peak_numbers = np.arange(1, len(peaks) + 1)
        slope, intercept = np.polyfit(peak_numbers, peaks, 1)
        differences = (peaks[4:] - peaks[:3]) / 4
        difference_result = float(np.mean(differences))
        reference = data["reference_excitation_voltage"]
        result = {
            "retarding_voltage": series["retarding_voltage"],
            "peaks": peaks.tolist(),
            "local_fits": local_fits,
            "difference_estimates": differences.tolist(),
            "difference_result": difference_result,
            "least_squares_slope": float(slope),
            "least_squares_intercept": float(intercept),
            "difference_relative_error_percent": abs(difference_result - reference) / reference * 100,
            "least_squares_relative_error_percent": abs(slope - reference) / reference * 100,
            "adjacent_spacings": np.diff(peaks).tolist(),
        }
        series_results.append(result)
        color = colors[series_index]
        label = rf"$U_{{G2A}}={series['retarding_voltage']:.2f}\,\mathrm{{V}}$"
        dense_voltage = np.linspace(0, 90, 1801)
        axes[0].plot(dense_voltage, PchipInterpolator(voltages, currents)(dense_voltage),
                     color=color, linewidth=0.8)
        axes[0].plot(voltages, currents, ".", color=color, markersize=2.1, label=label)
        for fit in local_fits:
            local_voltage = np.linspace(fit["sample_voltages"][0], fit["sample_voltages"][-1], 41)
            local_current = np.polyval(fit["coefficients"], local_voltage - fit["origin_voltage"])
            axes[0].plot(local_voltage, local_current, color=color, linewidth=1.3)
        axes[1].plot(peak_numbers, peaks, "o", color=color, markersize=3.5,
                     markerfacecolor="white", markeredgewidth=0.8, label=label)
        axes[1].plot(peak_numbers, intercept + slope * peak_numbers, "-", color=color, linewidth=0.9)
    axes[0].set(xlabel=r"$U_{G2K}\,/\,\mathrm{V}$", ylabel=r"$I_A\,/\,\mathrm{nA}$",
                xlim=(0, 90), ylim=(-4, 190), xticks=[0, 30, 60, 90])
    axes[1].set(xlabel=r"$n$", ylabel=r"$U_n\,/\,\mathrm{V}$",
                xlim=(0.6, 7.4), ylim=(5, 95), xticks=np.arange(1, 8))
    for axis in axes:
        axis.legend(frameon=False, loc="upper left", handlelength=1)
        axis.tick_params(direction="in", length=3)
    figure.tight_layout(pad=0.5, w_pad=1.3)
    figure.savefig("curves.pdf")
    plt.close(figure)
    with Path("transcribed.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["V_G2A_V", "V_G2K_V", "I_A_nA"])
        writer.writerows(raw_rows)
    Path("results.json").write_text(json.dumps(series_results, ensure_ascii=False, indent=2) + "\n")
    peak_tex = []
    peak_md = []
    result_tex = []
    result_md = []
    line_tex = []
    line_md = []
    for result in series_results:
        retarding = result["retarding_voltage"]
        peak_values = [f"{value:.2f}" for value in result["peaks"]]
        peak_tex.append(f"{retarding:.2f} & " + " & ".join(peak_values) + r" \\")
        peak_md.append(f"| {retarding:.2f} | " + " | ".join(peak_values) + " |")
        values = [
            f"{retarding:.2f}", f"{result['difference_result']:.2f}",
            f"{result['difference_relative_error_percent']:.2f}",
            f"{result['least_squares_slope']:.2f}",
            f"{result['least_squares_relative_error_percent']:.2f}",
        ]
        result_tex.append(" & ".join(values) + r" \\")
        result_md.append("| " + " | ".join(values) + " |")
        line_tex.append(
            rf"$U_{{G2A}}={retarding:.2f}\,\mathrm{{V}}$："
            rf"$U_n=({result['least_squares_intercept']:.3f}"
            rf"+{result['least_squares_slope']:.3f}n)\,\mathrm{{V}}$。"
        )
        line_md.append(
            f"$U_{{G2A}}={retarding:.2f}\\,\\mathrm{{V}}$："
            f"$U_n=({result['least_squares_intercept']:.3f}"
            f"+{result['least_squares_slope']:.3f}n)\\,\\mathrm{{V}}$。"
        )
    Path("numbers.tex").write_text(
        "\\newcommand{\\PeakRows}{\n" + "\n".join(peak_tex) + "\n}\n"
        "\\newcommand{\\ResultRows}{\n" + "\n".join(result_tex) + "\n}\n"
        "\\newcommand{\\FitLines}{\n" + r"\quad ".join(line_tex) + "\n}\n"
    )
    markdown = Path("postlab.md").read_text()
    for placeholder, value in {
        "{{PEAK_ROWS}}": "\n".join(peak_md),
        "{{RESULT_ROWS}}": "\n".join(result_md),
        "{{FIT_LINES}}": "\n\n".join(line_md),
    }.items():
        markdown = markdown.replace(placeholder, value)
    Path("report.md").write_text(markdown)


if __name__ == "__main__":
    main()
