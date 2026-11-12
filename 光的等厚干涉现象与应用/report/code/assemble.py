import json
import copy
import io
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def template_header(source_page):
    header = copy.copy(source_page)
    content = source_page.get_contents()
    operations = []
    depth = 0
    for operands, operator in content.operations:
        operations.append((operands, operator))
        if operator == b"q":
            depth += 1
        elif operator == b"Q":
            depth -= 1
        elif operator == b"f*":
            break
    else:
        raise ValueError("Template header rule not found")
    operations.extend(([], b"Q") for unused in range(depth))
    content.operations = operations
    stream = DecodedStreamObject()
    stream.set_data(content.get_data())
    header[NameObject("/Contents")] = stream
    text = header.extract_text()
    assert "大学物理实验报告" in text and "哈尔滨工业大学" in text
    assert "数据处理" not in text
    return header


def apply_template(postlab, original, workspace):
    header = template_header(original.pages[2])
    font = Path.home() / "Library/Containers/com.kingsoft.wpsoffice.mac/Data/.kingsoft/office6/data/fonts/online_ext_font_cache/HYZhongDengXianKW.ttf"
    pdfmetrics.registerFont(TTFont("TemplatePageNumber", str(font)))
    styled = PdfWriter()
    for index, page in enumerate(postlab.pages, start=3):
        page.mediabox = copy.copy(original.pages[2].mediabox)
        page.cropbox = copy.copy(original.pages[2].cropbox)
        page.merge_page(header)
        buffer = io.BytesIO()
        footer = canvas.Canvas(buffer, pagesize=(595, 841.4757))
        footer.setFont("TemplatePageNumber", 8.9954649)
        footer.drawString(500.50666754, 841.4757 - 776.69 * 0.9994961, str(index))
        footer.save()
        buffer.seek(0)
        page.merge_page(PdfReader(buffer).pages[0])
        styled.add_page(page)
    styled.write(workspace / "postlab.pdf")
    return PdfReader(workspace / "postlab.pdf")


def main():
    source = Path(sys.argv[1])
    workspace = Path(sys.argv[2])
    original = PdfReader(source)
    postlab = PdfReader(workspace / "postlab.pdf")
    assert len(original.pages) == 3
    assert len(postlab.pages) == 2
    postlab = apply_template(postlab, original, workspace)
    writer = PdfWriter()
    for page in original.pages[:2]:
        writer.add_page(page)
    for page in postlab.pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": "光的等厚干涉现象与应用实验报告"})
    writer.add_outline_item("一、预习", 0)
    writer.add_outline_item("二、原始数据记录", 1)
    writer.add_outline_item("三、数据处理", 2)
    writer.add_outline_item("不确定度、结论及讨论", 3)
    destination = workspace / "report.pdf"
    writer.write(destination)
    final = PdfReader(destination)
    assert len(final.pages) == 4
    for pdf, prefix, extra in (
        (source, "source", ["-f", "1", "-l", "3"]),
        (destination, "final", []),
        (workspace / "postlab.pdf", "postlab", []),
    ):
        subprocess.run(
            ["pdftoppm", *extra, "-r", "150", "-png", str(pdf), str(workspace / prefix)],
            check=True,
        )
    for index in (1, 2):
        with Image.open(workspace / f"source-{index}.png") as expected:
            with Image.open(workspace / f"final-{index}.png") as actual:
                assert actual.size == expected.size
                assert ImageChops.difference(actual.convert("RGB"), expected.convert("RGB")).getbbox() is None
    header_pixels = (0, 0, 1240, round(65 * 150 / 72))
    with Image.open(workspace / "source-3.png") as template:
        for index in (3, 4):
            with Image.open(workspace / f"final-{index}.png") as actual:
                assert ImageChops.difference(
                    actual.crop(header_pixels).convert("RGB"),
                    template.crop(header_pixels).convert("RGB"),
                ).getbbox() is None
    footer_pixels = (round(495 * 150 / 72), round(765 * 150 / 72), round(510 * 150 / 72), round(785 * 150 / 72))
    with Image.open(workspace / "source-3.png") as template:
        with Image.open(workspace / "final-3.png") as actual:
            assert ImageChops.difference(
                actual.crop(footer_pixels).convert("RGB"),
                template.crop(footer_pixels).convert("RGB"),
            ).getbbox() is None
    for index in (1, 2):
        with Image.open(workspace / f"postlab-{index}.png") as expected:
            with Image.open(workspace / f"final-{index+2}.png") as actual:
                assert actual.size == expected.size
                assert ImageChops.difference(actual.convert("RGB"), expected.convert("RGB")).getbbox() is None
    verification = {
        "total_pages": len(final.pages), "postlab_pages": len(postlab.pages),
        "pixel_identical_original_pages_150dpi": [1, 2],
        "postlab_matches_final_pages": [3, 4],
        "blank_original_pages_excluded": [3],
        "bookmarks": 4,
        "pixel_identical_template_headers_150dpi": [3, 4],
        "pixel_identical_template_page_number_150dpi": [3],
    }
    (workspace / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
