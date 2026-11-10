import argparse
from pathlib import Path

import pdfplumber


FONTS = {
    "HYKaiTiKW": "Kai",
    "HYShuSongErKW": "Song",
    "HYZhongHeiKW": "Hei",
    "HYZhongDengXianKW": "Deng",
    "TimesNewRomanPSMT": "Times",
    "TimesNewRomanPS-ItalicMT": "Italic",
    "TimesNewRomanPS-BoldMT": "Bold",
}


def escape(text):
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    commands = [r"\input{layout.tex}", r"\begin{document}"]
    with pdfplumber.open(arguments.source) as document:
        for page in document.pages:
            commands.append(r"\ReportPage{%")
            for rectangle in page.rects:
                commands.append(
                    rf"\put({rectangle['x0']:.4f},{rectangle['y0']:.4f})"
                    rf"{{\rule{{{rectangle['width']:.4f}bp}}{{{rectangle['height']:.4f}bp}}}}%"
                )
            for line in page.lines:
                width = line["linewidth"]
                if line["height"] < 0.001:
                    commands.append(
                        rf"\put({line['x0']:.4f},{line['y0'] - width / 2:.4f})"
                        rf"{{\rule{{{line['width']:.4f}bp}}{{{width:.4f}bp}}}}%"
                    )
                elif line["width"] < 0.001:
                    commands.append(
                        rf"\put({line['x0'] - width / 2:.4f},{line['y0']:.4f})"
                        rf"{{\rule{{{width:.4f}bp}}{{{line['height']:.4f}bp}}}}%"
                    )
                else:
                    raise ValueError("Unexpected diagonal line")
            for character in page.chars:
                if not character["text"].strip():
                    continue
                font = FONTS[character["fontname"].split("+")[-1]]
                if font == "Song" and character["size"] >= 12:
                    font = "SongHeavy"
                if font == "Kai" and character["size"] > 15:
                    font = "KaiHeavy"
                commands.append(
                    rf"\put({character['matrix'][4]:.4f},{character['matrix'][5]:.4f})"
                    rf"{{\hbox{{\{font}\fontsize{{{character['size']:.4f}bp}}"
                    rf"{{{character['size']:.4f}bp}}\selectfont "
                    + escape(character["text"]) + "}}%"
                )
            commands.append("}")
    commands.append(r"\end{document}")
    arguments.output.write_text("\n".join(commands) + "\n")


if __name__ == "__main__":
    main()
