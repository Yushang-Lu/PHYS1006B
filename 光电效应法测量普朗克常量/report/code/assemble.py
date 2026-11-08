from pathlib import Path
import argparse

from pypdf import PdfReader, PdfWriter


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root.parent / "report.pdf")
    output_path = parser.parse_args().output.resolve()
    template = PdfReader(root / "main.pdf")
    postlab = PdfReader(root / "postlab.pdf")
    assert len(template.pages) == 4
    assert len(postlab.pages) == 2
    writer = PdfWriter()
    for page in [*template.pages[:2], *postlab.pages]:
        writer.add_page(page)
    writer.add_outline_item("实验预习", 0)
    writer.add_outline_item("实验现象及原始数据记录", 1)
    writer.add_outline_item("数据处理与实验结论", 2)
    writer.add_outline_item("讨论题", 3)
    writer.add_metadata({"/Title": "光电效应法测定普朗克常量实验报告"})
    with output_path.open("wb") as output:
        writer.write(output)
    result = PdfReader(output_path)
    assert len(result.pages) == 4
    for index in range(2):
        assert (
            result.pages[index].get_contents().get_data()
            == template.pages[index].get_contents().get_data()
        )
    print(f"Created {output_path}; first two page content streams unchanged.")


if __name__ == "__main__":
    main()
