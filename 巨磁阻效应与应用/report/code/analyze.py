import csv
import json
from pathlib import Path
import re
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


def configure_plotting():
    font_path = subprocess.check_output(
        ["kpsewhich", "FandolHei-Regular.otf"], text=True
    ).strip()
    font_manager.fontManager.addfont(font_path)
    family = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams.update({
        "font.family": [family, "DejaVu Sans"],
        "mathtext.fontset": "stix",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "lines.linewidth": 1.15,
        "lines.markersize": 3.2,
        "legend.frameon": False,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    })


def pair(axis, horizontal, decreasing, increasing, quantity):
    axis.plot(horizontal, decreasing, "o-", color="#24537b", label=f"减小{quantity}")
    axis.plot(horizontal[::-1], increasing[::-1], "s--", color="#a14d24", label=f"增大{quantity}")
    axis.legend(fontsize=9)
    axis.tick_params(direction="in")


def render_markdown(source):
    lines = source.splitlines()
    output = []
    position = 0
    in_equation = False
    while position < len(lines):
        line = lines[position]
        if line == "$$":
            output.append(r"\]" if in_equation else r"\[")
            in_equation = not in_equation
        elif in_equation:
            output.append(line)
        elif line == r"\newpage":
            output.append(r"\clearpage")
        elif line.startswith("# "):
            output.append(r"\ReportSection{" + line[2:] + "}")
        elif line.startswith("## "):
            output.append(r"\ReportSubsection{" + line[3:] + "}")
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
            if not match:
                raise ValueError(f"Malformed figure: {line}")
            output.append(r"\ReportFigure{" + match[2] + "}{" + match[1] + "}")
        elif line.startswith("|"):
            rows = []
            while position < len(lines) and lines[position].startswith("|"):
                row = [cell.strip() for cell in lines[position].strip("|").split("|")]
                if not all(re.fullmatch(r"[-:]+", cell) for cell in row):
                    rows.append(row)
                position += 1
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError("Inconsistent table width")
            output += [
                r"\begin{center}\fontsize{9bp}{12bp}\selectfont",
                r"\setlength{\tabcolsep}{5bp}\renewcommand{\arraystretch}{1.15}",
                r"\begin{tabular}{" + "l" + "c" * (len(rows[0]) - 1) + r"}\toprule",
                " & ".join(rows[0]) + r"\\ \midrule",
            ]
            output += [" & ".join(row) + r"\\" for row in rows[1:]]
            output += [r"\bottomrule\end{tabular}\end{center}"]
            continue
        else:
            output.append(line)
        position += 1
    if in_equation:
        raise ValueError("Unclosed display equation")
    return "\n".join(output) + "\n"


def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / "measurements.json").read_text(encoding="utf-8"))
    currents = np.array(data["IM_mA"], dtype=float)
    for name in ("U_decreasing_mV", "U_increasing_mV", "IR_decreasing_mA", "IR_increasing_mA"):
        if len(data[name]) != len(currents) or len(currents) != 23:
            raise ValueError(f"Expected 23 readings: {name}")
    coefficient = 4 * np.pi * 1e-7 * data["coil_density_per_m"] * 1e-3 * 1e4
    field = coefficient * currents
    numerator = 1000 * data["voltage_V"]
    resistance = [
        numerator / np.array(data[name])
        for name in ("IR_decreasing_mA", "IR_increasing_mA")
    ]
    if not all(np.all(np.isfinite(values) & (values > 0)) for values in resistance):
        raise ValueError("Invalid resistance currents")
    configure_plotting()
    figure, axes = plt.subplots(2, 1, figsize=(6.1, 5.45), layout="constrained")
    pair(axes[0], field, np.array(data["U_decreasing_mV"]), np.array(data["U_increasing_mV"]), "磁场")
    pair(axes[1], field, *resistance, "磁场")
    for axis in axes:
        axis.set_xlabel(r"$B\,/\,\mathrm{Gauss}$")
        axis.set_xticks(np.arange(-30, 31, 10))
    axes[0].set_ylabel(r"$U_{\mathrm{out}}\,/\,\mathrm{mV}$")
    axes[1].set_ylabel(r"$R\,/\,\Omega$")
    figure.savefig("characteristics.pdf")
    plt.close(figure)

    thresholds = [switch["IM_mA"] * coefficient for switch in data["switches"]]
    low, high = data["switch_low_V"], data["switch_high_V"]
    symbolic = low is None or high is None
    if symbolic:
        low, high = 0, 1
    if high <= low:
        raise ValueError("Switch high level must exceed low level")
    figure, axes = plt.subplots(1, 2, figsize=(6.1, 1.95), layout="constrained")
    for axis, direction, color, negative, positive in (
        (axes[0], "减小磁场", "#24537b", thresholds[1], thresholds[0]),
        (axes[1], "增大磁场", "#a14d24", thresholds[2], thresholds[3]),
    ):
        axis.plot([-8, negative, negative, positive, positive, 8],
                  [high, high, low, low, high, high], color=color)
        axis.set_yticks([low, high], ["低", "高"] if symbolic else [f"{low:g}", f"{high:g}"])
        axis.set_ylim(low - (high - low) * 0.2, high + (high - low) * 0.25)
        axis.set_xticks([negative, 0, positive])
        axis.set_xticklabels([f"{negative:.3f}", "0", f"{positive:.3f}"])
        axis.set_xlabel(r"$B\,/\,\mathrm{Gauss}$")
        axis.set_ylabel("输出电平" if symbolic else r"$U_{\mathrm{out}}\,/\,\mathrm{V}$")
        axis.set_title(direction, fontsize=10)
    figure.savefig("switch.pdf")
    plt.close(figure)

    current_test = np.array(data["current_test_mA"])
    curves = data["current_curves"]
    if len(current_test) != 7 or len(curves) != 4:
        raise ValueError("Expected four current curves with seven readings")
    slopes = []
    for curve in curves:
        if len(curve["U_mV"]) != 7:
            raise ValueError("Expected seven current readings")
        slope, intercept = np.polyfit(current_test, curve["U_mV"], 1)
        slopes.append({"slope_mV_per_mA": float(slope), "intercept_mV": float(intercept)})
    figure, axes = plt.subplots(1, 2, figsize=(6.1, 2.15), layout="constrained")
    for index, axis in enumerate(axes):
        pair(axis, current_test, np.array(curves[2 * index]["U_mV"]),
             np.array(curves[2 * index + 1]["U_mV"]), "电流")
        axis.set_title(curves[2 * index]["bias"], fontsize=10)
        axis.set_xlabel(r"$I\,/\,\mathrm{mA}$")
        axis.set_ylabel(r"$U_{\mathrm{out}}\,/\,\mathrm{mV}$")
        axis.set_xticks([-300, 0, 300])
        axis.set_ylim((21, 28) if index == 0 else (147, 154))
    figure.savefig("current.pdf")
    plt.close(figure)

    angles, voltages = data["angle_deg"], data["angle_U_mV"]
    if len(angles) != 17 or len(voltages) != 17:
        raise ValueError("Expected seventeen angle readings")
    figure, axis = plt.subplots(figsize=(6.1, 1.7), layout="constrained")
    axis.plot(angles, voltages, "o-", color="#24537b")
    axis.set_xlabel(r"$\theta\,/\,({}^\circ)$")
    axis.set_ylabel(r"$U_{\mathrm{out}}\,/\,\mathrm{mV}$")
    axis.set_xticks(np.arange(0, 49, 6))
    axis.set_yticks([-50, 0, 50])
    figure.savefig("angle.pdf")
    plt.close(figure)

    bits = data["bits_regions_1_to_8"]
    if len(bits) != 8 or len(data["readout_V"]) != 8:
        raise ValueError("Expected eight magnetic-card regions")
    sorted_readings = sorted(data["readout_V"])
    gap_index = int(np.argmax(np.diff(sorted_readings)))
    read_threshold = (sorted_readings[gap_index] + sorted_readings[gap_index + 1]) / 2
    read_bits = "".join("1" if voltage > read_threshold else "0" for voltage in data["readout_V"])
    zero = data["IM_mA"].index(0)
    values = {
        "density": str(data["coil_density_per_m"]),
        "coefficient": f"{coefficient:.6f}",
        "resistance_numerator": f"{numerator:g}",
        "example_field": f"{field[0]:.3f}",
        "example_resistance": f"{resistance[0][0]:.0f}",
        "zero_down": str(data["U_decreasing_mV"][zero]),
        "zero_up": str(data["U_increasing_mV"][zero]),
        "switch_down_off": f"{thresholds[0]:.3f}",
        "switch_down_on": f"{thresholds[1]:.3f}",
        "switch_up_off": f"{thresholds[2]:.3f}",
        "switch_up_on": f"{thresholds[3]:.3f}",
        "bits_row": " | ".join(bits),
        "read_bits_row": " | ".join(read_bits),
        "readout_row": " | ".join(f"{voltage:.3f}" for voltage in data["readout_V"]),
        "bits": bits,
        "decimal": str(int(bits, 2)),
    }
    values.update({f"slope_{index}": f"{entry['slope_mV_per_mA']:.5f}" for index, entry in enumerate(slopes)})
    markdown = (root / "postlab.md").read_text(encoding="utf-8")
    markdown = re.sub(r"@@(\w+)@@", lambda match: values[match[1]], markdown)
    if not symbolic:
        markdown = markdown.replace("纵轴以低、高电平表示输出状态", "纵轴为实测输出电压")
    Path("report.md").write_text(markdown, encoding="utf-8")
    Path("body.tex").write_text(render_markdown(markdown), encoding="utf-8")
    Path("results.json").write_text(json.dumps({
        "B_Gauss_per_mA": coefficient,
        "thresholds_Gauss": thresholds,
        "switch_symbolic": symbolic,
        "current_fits": slopes,
        "decimal": int(bits, 2),
        "read_bits": read_bits,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with Path("converted.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["IM_mA", "B_Gauss", "R_decreasing_ohm", "R_increasing_ohm"])
        writer.writerows(zip(currents, field, *resistance))


if __name__ == "__main__":
    main()
