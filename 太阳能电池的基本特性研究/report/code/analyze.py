import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


def main():
    data = json.loads(Path("assets/measurements.json").read_text())
    font = Path.home() / "Library/Containers/com.kingsoft.wpsoffice.mac/Data/.kingsoft/office6/data/fonts/online_ext_font_cache/HYShuSongErKW.ttf"
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({
        "font.family": font_manager.FontProperties(fname=str(font)).get_name(),
        "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "axes.unicode_minus": False, "axes.spines.top": False,
        "axes.spines.right": False, "pdf.fonttype": 42,
        "mathtext.fontset": "stix", "lines.linewidth": 0.9,
    })
    irradiance = np.array(data["irradiance_W_m2"])
    same_light = np.flatnonzero(irradiance == data["output_irradiance_W_m2"])
    assert len(same_light) == 1
    index_light = int(same_light[0])
    input_power = data["area_m2"] * data["output_irradiance_W_m2"]
    figure, axes = plt.subplots(3, 2, figsize=(5.77, 4.1))
    figure.subplots_adjust(left=0.105, right=0.98, bottom=0.095, top=0.98, hspace=0.61, wspace=0.38)
    results, powers, result_rows, power_rows = [], [], [], []
    for index, sample in enumerate(data["samples"]):
        voltage = np.array(sample["output_voltage_V"])
        current = np.array(sample["output_current_mA"])
        assert len(voltage) == len(current)
        assert np.all(np.diff(voltage) > 0)
        power = voltage * current * 1e-3
        peak = int(np.argmax(power))
        assert 0 < peak < len(power) - 1
        result = {
            "name": sample["name"],
            "peak_voltage_V": float(voltage[peak]),
            "peak_current_mA": float(current[peak]),
            "max_power_W": float(power[peak]),
            "optimal_load_ohm": float(voltage[peak] / (current[peak] * 1e-3)),
            "open_voltage_V": sample["open_voltage_V"][index_light],
            "short_current_mA": float(current[0]),
            "fill_factor": float(power[peak] / (sample["open_voltage_V"][index_light] * current[0] * 1e-3)),
            "efficiency": float(power[peak] / input_power),
        }
        results.append(result)
        for value_voltage, value_current, value_power in zip(voltage, current, power):
            powers.append([sample["name"], value_voltage, value_current, value_power])
        style = dict(marker=("o", "s")[index], markersize=2.5, color=("#205482", "#b4522d")[index], label=sample["name"])
        dark_voltage = np.array(data["dark_voltage_V"])
        dark_current = np.array(sample["dark_current_mA"])
        assert len(dark_voltage) == len(dark_current)
        axes[0, 0].plot(dark_voltage, dark_current, **style)
        axes[0, 1].plot(dark_voltage[dark_voltage <= 0], dark_current[dark_voltage <= 0], **style)
        order = np.argsort(irradiance)
        axes[1, 0].plot(irradiance[order], np.array(sample["open_voltage_V"])[order], **style)
        axes[1, 1].plot(irradiance[order], np.array(sample["short_current_mA"])[order], **style)
        axes[2, 0].plot(voltage, current, **style)
        axes[2, 1].plot(voltage, power * 1000, **style)
        result_rows.append(
            f"{sample['name']} & {voltage[peak]:.2f} & {current[peak]:.3f} & "
            f"{power[peak] * 1000:.3f} & {result['optimal_load_ohm']:.1f} & "
            f"{result['fill_factor']:.3f} & {100 * result['efficiency']:.3f}" + r" \\"
        )
    labels = [
        (r"$V$ / V", r"$I_\mathrm{dark}$ / mA"),
        (r"$V$ / V", r"$I_\mathrm{dark}$ / mA"),
        (r"$E$ / (W m$^{-2}$)", r"$V_\mathrm{OC}$ / V"),
        (r"$E$ / (W m$^{-2}$)", r"$I_\mathrm{SC}$ / mA"),
        (r"$V$ / V", r"$I$ / mA"),
        (r"$V$ / V", r"$P_\mathrm{o}$ / mW"),
    ]
    for axis, (horizontal, vertical) in zip(axes.flat, labels):
        axis.set_xlabel(horizontal, labelpad=1)
        axis.set_ylabel(vertical, labelpad=1)
        axis.tick_params(labelsize=7, length=2, pad=1)
    axes[0, 0].legend(frameon=False, loc="upper left")
    figure.savefig("curves.pdf")
    plt.close(figure)
    Path("results.json").write_text(json.dumps({"input_power_W": input_power, "samples": results}, ensure_ascii=False, indent=2))
    with Path("powers.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample", "voltage_V", "current_mA", "power_W"])
        writer.writerows(powers)
    Path("results.tex").write_text(
        r"\begin{tabular}{lrrrrrr}\toprule" + "\n"
        r"电池 & $V_m$/V & $I_m$/mA & $P_{\max}$/mW & $R_m$/$\Omega$ & $FF$ & $\eta$/\% \\\midrule"
        + "\n" + "\n".join(result_rows) + "\n" + r"\bottomrule\end{tabular}"
    )
    for index in range(max(len(sample["output_voltage_V"]) for sample in data["samples"])):
        row = []
        for sample in data["samples"]:
            if index < len(sample["output_voltage_V"]):
                voltage = sample["output_voltage_V"][index]
                current = sample["output_current_mA"][index]
                row.extend([f"{voltage:g}", f"{voltage * current * 1e-3:.8f}".rstrip("0").rstrip(".")])
            else:
                row.extend(["", ""])
        power_rows.append(" & ".join(row) + r" \\")
    Path("power-table.tex").write_text(
        r"\begin{tabular}{rrrr}\toprule"
        r"\multicolumn{2}{c}{多晶硅}&\multicolumn{2}{c}{非晶硅}\\"
        r"$V$/V & $P_\mathrm{o}$/W & $V$/V & $P_\mathrm{o}$/W\\\midrule"
        + "\n" + "\n".join(power_rows) + "\n" + r"\bottomrule\end{tabular}"
    )
    Path("parameters.tex").write_text(
        rf"\(E={data['output_irradiance_W_m2']:g}\,\mathrm{{W/m^2}}\)，"
        rf"\(S={data['area_m2']:g}\,\mathrm{{m^2}}\)，"
        rf"\(P_{{\rm in}}=SE={input_power:.5f}\,\mathrm W\)。" + "\n"
    )
    tokens = {
        "POLY_POWER": f"{results[0]['max_power_W'] * 1000:.2f}",
        "AMORPHOUS_POWER": f"{results[1]['max_power_W'] * 1000:.2f}",
        "RATIO": f"{results[0]['max_power_W'] / results[1]['max_power_W']:.2f}",
        "IRRADIANCE": f"{data['output_irradiance_W_m2']:g}",
        "AREA": f"{data['area_m2']:g}",
        "INPUT_POWER": f"{input_power:.5f}",
        "POLY_VOC": f"{results[0]['open_voltage_V']:.2f}",
        "AMORPHOUS_VOC": f"{results[1]['open_voltage_V']:.2f}",
    }
    for name, value in tokens.items():
        Path(name.lower() + ".tex").write_text(value)
    markdown = Path("postlab.md").read_text()
    for name, value in tokens.items():
        markdown = markdown.replace("{{" + name + "}}", value)
    markdown += "\n\n|电池|Vm/V|Im/mA|Pmax/mW|Rm/Ω|FF|η/%|\n|---|---:|---:|---:|---:|---:|---:|\n"
    for result in results:
        markdown += (
            f"|{result['name']}|{result['peak_voltage_V']:.2f}|{result['peak_current_mA']:.3f}|"
            f"{result['max_power_W'] * 1000:.3f}|{result['optimal_load_ohm']:.1f}|"
            f"{result['fill_factor']:.3f}|{100 * result['efficiency']:.3f}|\n"
        )
    markdown += "\n\n表3续：各测量点的输出功率（$P_{\\rm o}=VI$，单位 W）\n\n|多晶硅 V/V|Po/W|非晶硅 V/V|Po/W|\n|---:|---:|---:|---:|\n"
    markdown += "\n".join("|" + row.replace(r" \\", "").replace(" & ", "|") + "|" for row in power_rows)
    Path("analysis.md").write_text(markdown + "\n")


if __name__ == "__main__":
    main()
