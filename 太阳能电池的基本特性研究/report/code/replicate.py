import argparse
from pathlib import Path

import pdfplumber
from pypdf import PdfReader
from pypdf.generic import ContentStream


FONTS = {
    "HYKaiTiKW": "Kai",
    "HYShuSongErKW": "Song",
    "HYZhongHeiKW": "Hei",
    "HYZhongDengXianKW": "Deng",
    "TimesNewRomanPSMT": "Times",
    "TimesNewRomanPS-ItalicMT": "Italic",
    "TimesNewRomanPS-BoldMT": "Bold",
    "TimesNewRomanPS-BoldItalicMT": "BoldItalic",
    "KingsoftSign": "Sign",
}


def escape(text):
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "$": r"\$",
        "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in text)


def stroke_weights(page, reader):
    mode, width = 0, 1
    stack, weights = [], []
    for arguments, operator in ContentStream(page.get_contents(), reader).operations:
        if operator == b"q":
            stack.append((mode, width))
        elif operator == b"Q":
            mode, width = stack.pop()
        elif operator == b"Tr":
            mode = int(arguments[0])
        elif operator == b"w":
            width = float(arguments[0])
        elif operator == b"Tj":
            text = arguments[0]
            encoded = text.original_bytes if hasattr(text, "original_bytes") else bytes(text)
            assert len(encoded) % 2 == 0
            weights.extend([width if mode == 2 else 0] * (len(encoded) // 2))
    return weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    reader = PdfReader(arguments.source)
    commands = [r"\input{layout.tex}", r"\begin{document}"]
    with pdfplumber.open(arguments.source) as document:
        for page_index, page in enumerate(document.pages):
            assert abs(page.width - 595.3) < 0.01
            assert abs(page.height - 841.9) < 0.01
            assert not page.images and not page.curves
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
            weights = stroke_weights(reader.pages[page_index], reader)
            for character, weight in zip(page.chars, weights, strict=True):
                if not character["text"].strip():
                    continue
                font = FONTS[character["fontname"].split("+")[-1]]
                slant = ""
                if weight:
                    slant += rf"\addfontfeatures{{FakeBold={100 * weight / character['size']:.5f}}}"
                if font == "Sign" and character["matrix"][2]:
                    slant = r"\addfontfeatures{FakeSlant=0.32258}"
                commands.append(
                    rf"\put({character['matrix'][4]:.4f},{character['matrix'][5]:.4f})"
                    rf"{{\hbox{{\{font}{slant}\fontsize{{{character['size']:.4f}bp}}"
                    rf"{{{character['size']:.4f}bp}}\selectfont{{}}"
                    + escape(character["text"]) + "}}%"
                )
            commands.append("}")
    commands.append(r"\end{document}")
    arguments.output.write_text("\n".join(commands) + "\n")


if __name__ == "__main__":
    main()
