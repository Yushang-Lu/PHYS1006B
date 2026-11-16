import argparse
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter


def save_page(page, destination):
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    original = PdfReader(arguments.source)
    template = PdfReader("main.pdf")
    overlay = PdfReader("postlab.pdf")
    if len(original.pages) != 3 or len(template.pages) != 3 or len(overlay.pages) != 1:
        raise ValueError("原记录、模板应为三页，课后内容应为一页")
    save_page(original.pages[0], "prelab.pdf")
    save_page(original.pages[1], "raw.pdf")
    page = template.pages[2]
    page.merge_page(overlay.pages[0])
    save_page(page, "postlab-rendered.pdf")
    subprocess.run([
        sys.executable, "assemble_report.py",
        "--prelab", "prelab.pdf", "--raw", "raw.pdf",
        "--postlab", "postlab-rendered.pdf", "--output", "report.pdf",
        "--title", "双光栅检测微弱振动实验报告",
    ], check=True)
    result = PdfReader("report.pdf")
    if len(result.pages) != 3:
        raise ValueError("完整报告必须为三页")
    for index in range(2):
        if original.pages[index].get_contents().get_data() != result.pages[index].get_contents().get_data():
            raise ValueError("保留页内容流发生变化")
        if original.pages[index].mediabox != result.pages[index].mediabox:
            raise ValueError("保留页尺寸发生变化")
    Path("qa").mkdir(exist_ok=True)
    for label, path, count in (
        ("original-data", arguments.source, 2),
        ("report", Path("report.pdf"), 3),
        ("postlab", Path("postlab-rendered.pdf"), 1),
    ):
        subprocess.run([
            "pdftoppm", "-r", "144", "-f", "1", "-l", str(count),
            "-png", str(path), f"qa/{label}",
        ], check=True)
    for before_name, after_name in (
        ("original-data-1", "report-1"),
        ("original-data-2", "report-2"),
        ("postlab-1", "report-3"),
    ):
        before = Image.open(f"qa/{before_name}.png").convert("RGB")
        after = Image.open(f"qa/{after_name}.png").convert("RGB")
        if before.size != after.size or ImageChops.difference(before, after).getbbox():
            raise ValueError(f"像素比较失败：{before_name}, {after_name}")
    Path("report-validation.json").write_text(json.dumps({
        "pages": 3,
        "preserved_pages_content_stream_identical": [1, 2],
        "preserved_pages_pixel_identical_at_144_dpi": [1, 2],
        "standalone_postlab_matches_final_page": True,
    }, indent=2) + "\n")
    print("原前两页内容流、尺寸及144 dpi像素完全一致；独立课后页与拼接页一致。")


if __name__ == "__main__":
    main()
