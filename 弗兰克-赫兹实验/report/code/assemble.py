import argparse
from pathlib import Path
import subprocess

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    source = PdfReader(arguments.source)
    overlay = PdfReader("postlab.pdf")
    if len(source.pages) != 4 or len(overlay.pages) != 2:
        raise ValueError("原报告必须4页，补写内容必须2页")
    writer = PdfWriter()
    postlab_writer = PdfWriter()
    for index, page in enumerate(source.pages):
        if index >= 2:
            page.merge_page(overlay.pages[index - 2])
            postlab_writer.add_page(page)
        writer.add_page(page)
    writer.add_outline_item("实验预习", 0)
    writer.add_outline_item("原始数据记录", 1)
    writer.add_outline_item("数据处理及实验结论", 2)
    writer.add_outline_item("讨论题", 3)
    writer.add_metadata({"/Title": "弗兰克-赫兹实验报告"})
    writer.write("report.pdf")
    postlab_writer.write("postlab-rendered.pdf")
    original = PdfReader(arguments.source)
    result = PdfReader("report.pdf")
    for index in range(2):
        if original.pages[index].get_contents().get_data() != result.pages[index].get_contents().get_data():
            raise ValueError(f"第{index + 1}页内容流发生变化")
        if original.pages[index].mediabox != result.pages[index].mediabox:
            raise ValueError("保留页尺寸发生变化")
    Path("qa").mkdir(exist_ok=True)
    for label, path, page_count in (
        ("original", arguments.source, 2),
        ("report", Path("report.pdf"), 4),
        ("postlab", Path("postlab-rendered.pdf"), 2),
    ):
        subprocess.run([
            "pdftoppm", "-r", "144", "-f", "1", "-l", str(page_count),
            "-png", str(path), f"qa/{label}",
        ], check=True)
    for index in range(1, 3):
        before = Image.open(f"qa/original-{index}.png").convert("RGB")
        after = Image.open(f"qa/report-{index}.png").convert("RGB")
        if before.size != after.size or ImageChops.difference(before, after).getbbox():
            raise ValueError(f"第{index}页像素比较不一致")
        standalone = Image.open(f"qa/postlab-{index}.png").convert("RGB")
        merged = Image.open(f"qa/report-{index + 2}.png").convert("RGB")
        if standalone.size != merged.size or ImageChops.difference(standalone, merged).getbbox():
            raise ValueError("课后页与拼接页不一致")
    print("原预习和数据记录页：内容流、尺寸、144 dpi像素均完全一致。")


if __name__ == "__main__":
    main()
