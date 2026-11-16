from pathlib import Path
import argparse
import subprocess

from pypdf import PdfReader, PdfWriter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    source = PdfReader(arguments.source)
    overlay = PdfReader("postlab.pdf")
    if len(source.pages) != 5 or len(overlay.pages) != 2:
        raise ValueError("预期原始记录5页、课后正文2页。")
    final = PdfWriter()
    postlab = PdfWriter()
    for index, page in enumerate(source.pages):
        if index >= 3:
            page.merge_page(overlay.pages[index - 3])
            postlab.add_page(page)
        final.add_page(page)
    final.add_outline_item("实验预习", 0)
    final.add_outline_item("原始数据记录", 1)
    final.add_outline_item("数据处理", 3)
    final.add_outline_item("实验结论与讨论", 4)
    final.add_metadata({"/Title": "电子荷质比的测定", "/Subject": "作图法采用明确标注的假设半径试算"})
    final.write("report.pdf")
    postlab.write("postlab_complete.pdf")
    for label, path in (("original", arguments.source), ("final", Path("report.pdf"))):
        subprocess.run(
            ["pdftoppm", "-f", "1", "-l", "3", "-r", "100", str(path), label],
            check=True,
        )
    for number in range(1, 4):
        if Path(f"original-{number}.ppm").read_bytes() != Path(f"final-{number}.ppm").read_bytes():
            raise AssertionError(f"第{number}页像素不一致")
    assert len(PdfReader("report.pdf").pages) == 5
    print("校验通过：5页；前三页逐页100 dpi像素完全一致。")


if __name__ == "__main__":
    main()
