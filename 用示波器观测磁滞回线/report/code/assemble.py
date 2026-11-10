from io import BytesIO
from pathlib import Path
import sys

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


def main():
    original = PdfReader(sys.argv[1])
    template = PdfReader("main.pdf")
    content = PdfReader("postlab.pdf")
    assert len(original.pages) == len(template.pages) == 4
    assert len(content.pages) == 2
    record_path = Path("assets/原始记录.png")
    image = Image.open(record_path)
    width = 418.0
    height = width * image.height / image.width
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(595.3, 841.9))
    canvas.setFillColorRGB(1, 1, 1)
    canvas.rect(87, 841.9 - 690, 425, 600, fill=1, stroke=0)
    canvas.drawImage(str(record_path), 88.7, 841.9 - 92 - height, width=width, height=height)
    canvas.save()
    stream.seek(0)
    original.pages[1].merge_page(PdfReader(stream).pages[0])
    report = PdfWriter()
    report.add_page(original.pages[0])
    report.add_page(original.pages[1])
    postlab = PdfWriter()
    for index in range(2):
        page = template.pages[index + 2]
        page.merge_page(content.pages[index])
        report.add_page(page)
        postlab.add_page(page)
    report.add_metadata({"/Title": "用示波器观测磁滞回线", "/Author": ""})
    report.write("report.pdf")
    postlab.write("postlab.pdf")
    assert original.pages[0].get_contents().get_data() == PdfReader("report.pdf").pages[0].get_contents().get_data()


if __name__ == "__main__":
    main()
