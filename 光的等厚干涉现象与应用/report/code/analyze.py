import json
import math
from decimal import Decimal
from pathlib import Path
import re

import numpy as np


def markdown_to_tex(markdown):
    lines = markdown.splitlines()
    output = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == "$$":
            output.append(r"\[")
            index += 1
            while index < len(lines) and lines[index] != "$$":
                output.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError("Unclosed display equation")
            output.append(r"\]")
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip("|").split("|")])
                index += 1
            output.extend([
                r"\begin{center}",
                r"\fontsize{10.5pt}{14pt}\selectfont",
                r"\setlength{\tabcolsep}{7pt}",
                r"\renewcommand{\arraystretch}{1.18}",
                r"\begin{tabular}{" + "r" * len(rows[0]) + "}",
                r"\toprule",
                " & ".join(rows[0]) + r" \\",
                r"\midrule",
            ])
            output.extend(" & ".join(row) + r" \\" for row in rows[2:])
            output.extend([r"\bottomrule", r"\end{tabular}", r"\end{center}"])
            continue
        elif line == "<!-- pagebreak -->":
            output.append(r"\newpage")
        elif line.startswith("### "):
            output.append(r"\subsection{" + line[4:] + "}")
        elif line.startswith("## "):
            output.append(r"\section{" + line[3:] + "}")
        else:
            output.append(line)
        index += 1
    return "\n".join(output) + "\n"


def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / "measurements.json").read_text())
    rings = data["rings"]
    assert [row["order"] for row in rings] == list(range(31, 9, -1))
    assert data["position_unit"] == "mm"
    assert all(re.fullmatch(r"\d+\.\d{3}", row[side]) for row in rings for side in ("left", "right"))
    wavelength = float(data["wavelength_nm"]) * 1e-6
    assert wavelength > 0
    diameters = np.array([abs(float(row["left"]) - float(row["right"])) for row in rings])
    assert np.all(diameters > 0)
    differences = diameters[:11] ** 2 - diameters[11:] ** 2
    assert np.all(differences > 0)
    decimal_diameters = [abs(Decimal(row["left"]) - Decimal(row["right"])) for row in rings]
    decimal_differences = [
        outer ** 2 - inner ** 2
        for outer, inner in zip(decimal_diameters[:11], decimal_diameters[11:])
    ]
    np.testing.assert_allclose(differences, [float(value) for value in decimal_differences], rtol=0, atol=1e-12)
    mean_difference = float(differences.mean())
    sum_squares = float(np.sum((differences - mean_difference) ** 2))
    uncertainty_difference = math.sqrt(sum_squares / (11 * 10))
    radius = mean_difference / (44 * wavelength)
    uncertainty_radius = uncertainty_difference / (44 * wavelength)
    individual_radii = differences / (44 * wavelength)
    np.testing.assert_allclose(radius, individual_radii.mean(), rtol=1e-14)
    np.testing.assert_allclose(uncertainty_radius, np.std(individual_radii, ddof=1) / math.sqrt(11), rtol=1e-12)
    table = [
        r"| $m$ | $n$ | $D_m/\mathrm{mm}$ | $D_n/\mathrm{mm}$ | $D_m^2/\mathrm{mm^2}$ | $D_n^2/\mathrm{mm^2}$ | $q_i/\mathrm{mm^2}$ |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    pairs = []
    for index, difference in enumerate(decimal_differences):
        outer = decimal_diameters[index]
        inner = decimal_diameters[index + 11]
        table.append(
            f"| {31-index} | {20-index} | {outer:.3f} | {inner:.3f} | "
            f"{outer**2:.6f} | {inner**2:.6f} | {difference:.6f} |"
        )
        pairs.append({
            "m": 31 - index, "n": 20 - index,
            "Dm_mm": str(outer), "Dn_mm": str(inner),
            "Dm_squared_mm2": str(outer ** 2), "Dn_squared_mm2": str(inner ** 2),
            "q_mm2": str(difference), "R_mm": float(individual_radii[index]),
        })
    uncertainty_m = uncertainty_radius / 1000
    decimals = 1 - math.floor(math.log10(uncertainty_m))
    replacements = {
        "LAMBDA": f'{data["wavelength_nm"]:.2f}',
        "LAMBDA_MM": f"{wavelength * 1e4:.5f}",
        "TABLE": "\n".join(table),
        "LEFT31": rings[0]["left"], "RIGHT31": rings[0]["right"],
        "LEFT20": rings[11]["left"], "RIGHT20": rings[11]["right"],
        "D31": f"{decimal_diameters[0]:.3f}", "D20": f"{decimal_diameters[11]:.3f}",
        "Q1": f"{decimal_differences[0]:.6f}",
        "SUMQ": f"{sum(decimal_differences):.6f}",
        "MEANQ": f"{mean_difference:.6f}",
        "R_MM": f"{radius:.3f}", "R_M": f"{radius / 1000:.6f}",
        "SSQ": f"{sum_squares:.6f}", "UQ": f"{uncertainty_difference:.6f}",
        "UR_MM": f"{uncertainty_radius:.3f}", "UR_M": f"{uncertainty_m:.6f}",
        "R_ROUNDED": f"{radius / 1000:.{decimals}f}",
        "UR_ROUNDED": f"{uncertainty_m:.{decimals}f}",
        "RELATIVE": f"{100 * uncertainty_radius / radius:.2f}",
    }
    markdown = (root / "report.md").read_text()
    for key, value in replacements.items():
        markdown = markdown.replace(f"@@{key}@@", value)
    assert "@@" not in markdown
    (root / "analysis.md").write_text(markdown)
    (root / "body.tex").write_text(markdown_to_tex(markdown))
    results = {
        "pairs": pairs, "wavelength_mm": wavelength,
        "mean_q_mm2": mean_difference, "sum_squared_deviations_mm4": sum_squares,
        "uA_mean_q_mm2": uncertainty_difference, "R_mm": radius,
        "uA_R_mm": uncertainty_radius,
        "relative_uA_percent": uncertainty_radius / radius * 100,
        "checks": ["44 readings", "11 disjoint pairs", "Decimal cross-check", "mean and standard error of individual radii"],
    }
    (root / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"R = ({replacements['R_ROUNDED']} ± {replacements['UR_ROUNDED']}) m (A 类)")


if __name__ == "__main__":
    main()
