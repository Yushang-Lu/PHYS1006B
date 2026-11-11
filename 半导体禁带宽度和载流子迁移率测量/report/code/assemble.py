import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter


def main():
    source = Path(sys.argv[1])
    workspace = Path(sys.argv[2])
    original = PdfReader(source)
    postlab = PdfReader(workspace / "postlab.pdf")
    assert len(original.pages) == 5
    writer = PdfWriter()
    for page in original.pages[:3]:
        writer.add_page(page)
    for page in postlab.pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": "半导体禁带宽度和载流子迁移率测量实验报告"})
    writer.add_outline_item("实验预习及原始记录", 0)
    writer.add_outline_item("数据处理、结论与讨论", 3)
    destination = workspace / "report.pdf"
    writer.write(destination)
    final = PdfReader(destination)
    assert len(final.pages) == 3 + len(postlab.pages)
    subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "3", "-r", "150", "-png", str(source), str(workspace / "source")],
        check=True,
    )
    subprocess.run(
        ["pdftoppm", "-r", "150", "-png", str(destination), str(workspace / "final")],
        check=True,
    )
    preserved = []
    for index in range(1, 4):
        with Image.open(workspace / f"source-{index}.png") as expected:
            with Image.open(workspace / f"final-{index}.png") as actual:
                assert actual.size == expected.size
                assert ImageChops.difference(actual.convert("RGB"), expected.convert("RGB")).getbbox() is None
                preserved.append(index)
    verification = {
        "total_pages": len(final.pages),
        "postlab_pages": len(postlab.pages),
        "pixel_identical_pages_150dpi": preserved,
        "original_pages_used": [1, 2, 3],
        "blank_original_pages_excluded": [4, 5],
    }
    (workspace / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
