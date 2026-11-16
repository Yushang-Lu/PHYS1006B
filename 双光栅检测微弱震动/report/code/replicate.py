import argparse
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


FONTS = {
    "HYKaiTiKW": "Kai",
    "HYShuSongErKW": "Song",
    "HYZhongHeiKW": "Hei",
    "HYZhongDengXianKW": "Deng",
    "TimesNewRomanPSMT": "Times",
}


def escape(text):
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "$": r"\$",
        "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    fonts = Path("fonts")
    fonts.mkdir(exist_ok=True)
    for page in PdfReader(arguments.source).pages:
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            name = str(font["/BaseFont"]).split("+")[-1]
            if name not in FONTS:
                raise ValueError(f"Unsupported font: {name}")
            descendant = font["/DescendantFonts"][0].get_object()
            embedded = descendant["/FontDescriptor"]["/FontFile2"].get_data()
            destination = fonts / f"{name}.ttf"
            if destination.exists() and destination.read_bytes() != embedded:
                raise ValueError(f"Conflicting font subsets: {name}")
            destination.write_bytes(embedded)
    commands = []
    with pdfplumber.open(arguments.source) as document:
        if len(document.pages) != 3:
            raise ValueError("Expected the three-page blank template")
        for page in document.pages:
            if page.images or page.curves or (page.width, page.height) != (595.3, 841.9):
                raise ValueError("Unsupported template geometry")
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
    Path("template.tex").write_text("\n".join(commands) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
