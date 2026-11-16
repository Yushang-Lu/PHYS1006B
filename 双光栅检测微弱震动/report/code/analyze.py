from decimal import Decimal
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter


def compact(value):
    return format(value.normalize(), "f")


def main():
    data = json.loads(Path("measurements.json").read_text())
    density = Decimal(data["grating_density_per_mm"])
    rows = data["sweep"]
    frequencies = [Decimal(row["frequency_hz"]) for row in rows]
    if density <= 0 or len(rows) != 9 or any(
        after <= before for before, after in zip(frequencies, frequencies[1:])
    ):
        raise ValueError("光栅密度、点数或频率顺序错误")
    for row in [data["resonance"], *rows]:
        count = Decimal(row["half_period_wave_count"])
        if count < 0:
            raise ValueError("波数必须非负")
        row["amplitude_mm"] = compact(count / (2 * density))
        row["amplitude_um"] = compact(count * 1000 / (2 * density))
    peak = max(rows, key=lambda row: Decimal(row["amplitude_um"]))
    values = {
        "Density": compact(density),
        "Denominator": compact(2 * density),
        "Scale": compact(1000 / (2 * density)),
        "ResFrequency": data["resonance"]["frequency_hz"],
        "ResCount": data["resonance"]["half_period_wave_count"],
        "ResAmplitude": data["resonance"]["amplitude_um"],
        "PeakFrequency": peak["frequency_hz"],
        "PeakAmplitude": peak["amplitude_um"],
    }
    commands = [rf"\newcommand{{\{key}}}{{{value}}}" for key, value in values.items()]
    for name, key in (
        ("FrequencyRow", "frequency_hz"),
        ("CountRow", "half_period_wave_count"),
        ("AmplitudeRow", "amplitude_um"),
    ):
        commands.append(rf"\newcommand{{\{name}}}{{" + " & ".join(row[key] for row in rows) + "}")
    Path("numbers.tex").write_text("\n".join(commands) + "\n")
    Path("results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    markdown = Path("postlab.md").read_text()
    for key, value in values.items():
        markdown = markdown.replace(f"@{key}@", value)
    table = "| $f/\\mathrm{Hz}$ | $N$ | $A/\\mu\\mathrm{m}$ |\n|---:|---:|---:|\n"
    table += "\n".join(
        f"| {row['frequency_hz']} | {row['half_period_wave_count']} | {row['amplitude_um']} |"
        for row in rows
    )
    Path("report.md").write_text(markdown.replace("@Table@", table))
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 9, "pdf.fonttype": 42})
    figure, axes = plt.subplots(figsize=(5.65, 2.15))
    figure.subplots_adjust(left=0.12, right=0.985, bottom=0.27, top=0.97)
    axes.plot(
        [float(value) for value in frequencies],
        [float(row["amplitude_um"]) for row in rows],
        color="black", marker="o", markersize=3.5, linewidth=0.9,
    )
    axes.set_xlabel(r"$f\ /\ \mathrm{Hz}$", labelpad=3)
    axes.set_ylabel(r"$A\ /\ \mu\mathrm{m}$", labelpad=4)
    axes.set_xticks([503.49, 503.69, 503.89, 504.09, 504.29])
    axes.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    axes.set_ylim(0, 115)
    axes.set_yticks([0, 25, 50, 75, 100])
    axes.spines[["top", "right"]].set_visible(False)
    axes.tick_params(direction="in")
    figure.savefig("curve.pdf")
    plt.close(figure)


if __name__ == "__main__":
    main()
