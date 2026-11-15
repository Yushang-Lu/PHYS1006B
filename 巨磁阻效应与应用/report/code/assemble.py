import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    source = PdfReader(arguments.source)
    postlab = PdfReader("postlab.pdf")
    if len(source.pages) != 6:
        raise ValueError("Expected six source pages")
    writer = PdfWriter()
    for page in source.pages[:4]:
        writer.add_page(page)
    for page in postlab.pages:
        writer.add_page(page)
    writer.add_outline_item("实验预习", 0)
    writer.add_outline_item("实验现象及原始数据记录", 1)
    writer.add_outline_item("数据处理、实验结论及讨论", 4)
    writer.add_metadata({"/Title": "巨磁阻效应与应用实验报告"})
    with Path("report.pdf").open("wb") as stream:
        writer.write(stream)
    result = PdfReader("report.pdf")
    for index in range(4):
        before, after = source.pages[index], result.pages[index]
        if before.get_contents().get_data() != after.get_contents().get_data():
            raise ValueError(f"Preserved page {index + 1} content changed")
        if list(before.mediabox) != list(after.mediabox):
            raise ValueError(f"Preserved page {index + 1} geometry changed")


if __name__ == "__main__":
    main()
