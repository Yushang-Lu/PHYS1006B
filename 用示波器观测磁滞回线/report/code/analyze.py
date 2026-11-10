import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def intercepts(horizontal, vertical):
    values = []
    for index in range(len(horizontal)):
        following = (index + 1) % len(horizontal)
        first = horizontal[index]
        second = horizontal[following]
        if first == 0:
            values.append(float(vertical[index]))
        elif first * second < 0:
            fraction = -first / (second - first)
            values.append(float(vertical[index] + fraction * (vertical[following] - vertical[index])))
    assert len(values) == 2
    return sorted(values)


def main():
    data = json.loads(Path("assets/measurements.json").read_text())
    results = []
    converted = []
    parameter_text = (
        rf"取 \(f={data['frequency_Hz']:g}\,\mathrm{{Hz}}\)，"
        rf"\(R_1={data['R1_ohm']:.1f}\,\Omega\)，"
        rf"\(R_2={data['R2_ohm'] / 1000:g}\,\mathrm{{k}}\Omega\)，"
        rf"\(C={data['C_F'] * 1e6:.1f}\,\mu\mathrm{{F}}\)。"
    )
    Path("parameters.tex").write_text(parameter_text + "\n")
    conversion_rows = [
        r"\begin{tabular}{c c c c c c}",
        r"\toprule 样品 & $N_1,N_2$ & $L/\mathrm m$ & $S/\mathrm{m^2}$ & $H/(\mathrm{A/m})$ & $B/\mathrm T$\\",
        r"\midrule",
    ]
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.0,
        "pdf.fonttype": 42,
    })
    figure, axes = plt.subplots(2, 2, figsize=(5.75, 3.25))
    for index, sample in enumerate(data["samples"]):
        scale_h = sample["N1"] / (sample["L_m"] * data["R1_ohm"]) * 0.001
        scale_b = data["R2_ohm"] * data["C_F"] / (sample["N2"] * sample["S_m2"]) * 0.001
        loop_h = np.asarray(sample["loop_Ux_mV"]) * scale_h
        loop_b = np.asarray(sample["loop_Uy_mV"]) * scale_b
        basic_h = np.asarray(sample["basic_Ux_mV"]) * scale_h
        basic_b = np.asarray(sample["basic_Uy_mV"]) * scale_b
        assert len(loop_h) == len(loop_b) == 20
        assert len(basic_h) == len(basic_b) == 10
        remanence = intercepts(loop_h, loop_b)
        coercivity = intercepts(loop_b, loop_h)
        result = {
            "sample": index + 1,
            "H_per_mV": scale_h,
            "B_per_mV": scale_b,
            "Br_signed_T": remanence,
            "Hc_signed_A_m": coercivity,
            "Br_T": float(np.mean(np.abs(remanence))),
            "Hc_A_m": float(np.mean(np.abs(coercivity))),
        }
        results.append(result)
        conversion_rows.append(
            f"{index + 1} & {sample['N1']},{sample['N2']} & {sample['L_m']:.3f} & "
            rf"${sample['S_m2'] * 1e4:.2f}\times10^{{-4}}$ & "
            rf"${scale_h:.6f}\,U_X$ & ${scale_b:.7f}\,U_Y$\\"
        )
        for kind, horizontal, vertical in (
            ("loop", loop_h, loop_b), ("basic", basic_h, basic_b),
        ):
            for number, (field_h, field_b) in enumerate(zip(horizontal, vertical), 1):
                converted.append([index + 1, kind, number, f"{field_h:.9g}", f"{field_b:.9g}"])
        loop_axis = axes[0, index]
        basic_axis = axes[1, index]
        loop_axis.plot(np.r_[loop_h, loop_h[0]], np.r_[loop_b, loop_b[0]], "-o", markersize=2.3, color="#194e78")
        basic_axis.plot(basic_h, basic_b, "-o", markersize=2.3, color="#194e78")
        for axis in (loop_axis, basic_axis):
            axis.axhline(0, color="0.6", linewidth=0.4, zorder=0)
            axis.axvline(0, color="0.6", linewidth=0.4, zorder=0)
            axis.set_xlabel(r"$H\;(\mathrm{A\,m^{-1}})$", labelpad=1)
            axis.set_ylabel(r"$B\;(\mathrm{T})$", labelpad=1)
            axis.tick_params(labelsize=7, width=0.5, length=2, pad=2)
        loop_axis.set_title(f"Sample {index + 1}", fontsize=8, pad=3)
        basic_axis.set_xlim(left=0)
        basic_axis.set_ylim(bottom=0)
    figure.subplots_adjust(left=0.105, right=0.985, bottom=0.12, top=0.93, hspace=0.55, wspace=0.36)
    figure.savefig("curves.pdf")
    plt.close(figure)
    Path("results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    with Path("converted.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample", "curve", "point", "H_A_per_m", "B_T"])
        writer.writerows(converted)
    rows = [
        r"\begin{tabular}{c r r r r r r}",
        r"\toprule 样品 & $B_{r+}$/T & $B_{r-}$/T & $B_r$/T & $H_{c-}/(\mathrm{A/m})$ & $H_{c+}/(\mathrm{A/m})$ & $H_c/(\mathrm{A/m})$\\",
        r"\midrule",
    ]
    for result in results:
        negative_b, positive_b = result["Br_signed_T"]
        negative_h, positive_h = result["Hc_signed_A_m"]
        rows.append(
            f"{result['sample']} & {positive_b:.3f} & {negative_b:.3f} & {result['Br_T']:.3f} & "
            f"{negative_h:.1f} & {positive_h:.1f} & {result['Hc_A_m']:.1f}" + r"\\"
        )
    rows.extend([r"\bottomrule", r"\end{tabular}"])
    Path("results.tex").write_text("\n".join(rows) + "\n")
    conversion_rows.extend([r"\bottomrule", r"\end{tabular}"])
    Path("conversion.tex").write_text("\n".join(conversion_rows) + "\n")
    markdown = Path("postlab.md").read_text()
    markdown = markdown.replace("{{PARAMETERS}}", parameter_text.replace(r"\(", "$").replace(r"\)", "$"))
    markdown_rows = [
        "| 样品 | $N_1,N_2$ | $L/\\mathrm m$ | $S/\\mathrm{m^2}$ | $H/(\\mathrm{A/m})$ | $B/\\mathrm T$ |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for sample, result in zip(data["samples"], results):
        markdown_rows.append(
            f"| {result['sample']} | {sample['N1']},{sample['N2']} | {sample['L_m']:.3f} | "
            f"{sample['S_m2']:.6f} | ${result['H_per_mV']:.6f}U_X$ | ${result['B_per_mV']:.7f}U_Y$ |"
        )
    markdown = markdown.replace("{{CONVERSION_TABLE}}", "\n".join(markdown_rows))
    for result in results:
        markdown = markdown.replace(f"{{{{BR{result['sample']}}}}}", f"{result['Br_T']:.3f}")
        markdown = markdown.replace(f"{{{{HC{result['sample']}}}}}", f"{result['Hc_A_m']:.1f}")
    Path("analysis.md").write_text(markdown)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
