import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageStat
from pypdf import PdfReader


def render(source, prefix):
    subprocess.run(["pdftoppm", "-r", "120", "-png", str(source), str(prefix)], check=True)
    return sorted(prefix.parent.glob(prefix.name + "-*.png"))


def difference(first, second):
    with Image.open(first) as left, Image.open(second) as right:
        assert left.size == right.size
        delta = ImageChops.difference(left.convert("L"), right.convert("L"))
        histogram = delta.histogram()
        return {
            "mean_absolute_gray_difference": ImageStat.Stat(delta).mean[0],
            "fraction_difference_gt_32": sum(histogram[33:]) / (left.width * left.height),
            "identical": delta.getbbox() is None,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parent
    directory = arguments.directory.resolve()
    assert not directory.is_relative_to(root.parent)
    original = root.parent.parent / "resource/实验6 太阳能电池的基本特性研究_20260915092644.pdf"
    source = render(original, directory / "original")
    replica = render(directory / "main.pdf", directory / "replica")
    comparisons = {"template": [difference(left, right) for left, right in zip(source, replica, strict=True)]}
    sheet = Image.new("RGB", (1000, 708 * 5), "white")
    for index, pair in enumerate(zip(source, replica, strict=True)):
        for column, path in enumerate(pair):
            image = Image.open(path).convert("RGB")
            image.thumbnail((500, 708))
            sheet.paste(image, (500 * column, 708 * index))
    sheet.save(directory / "template-comparison.png")
    if (directory / "report.pdf").exists():
        record = render(root / "assets/原始记录.pdf", directory / "record")
        final = render(directory / "report.pdf", directory / "final")
        postlab = render(directory / "postlab.pdf", directory / "postlab")
        comparisons["preserved"] = [difference(record[index], final[index]) for index in range(2)]
        with Image.open(record[2]) as original_image, Image.open(final[2]) as final_image:
            delta = ImageChops.difference(original_image.convert("RGB"), final_image.convert("RGB"))
            draw = ImageDraw.Draw(delta)
            for bounds in ((88, 390, 347, 650), (363, 398, 507, 520)):
                draw.rectangle(tuple(round(value * 120 / 72) for value in bounds), fill=(0, 0, 0))
            comparisons["record_outside_additions_identical"] = delta.getbbox() is None
            assert comparisons["record_outside_additions_identical"]
        comparisons["postlab"] = [difference(postlab[index], final[index + 3]) for index in range(2)]
        assert all(item["identical"] for item in comparisons["preserved"] + comparisons["postlab"])
        reader = PdfReader(directory / "report.pdf")
        assert len(reader.pages) == 5
        text = "\n".join(page.extract_text() for page in reader.pages[3:])
        (directory / "final-text.txt").write_text(text)
    (directory / "pixel-comparison.json").write_text(json.dumps(comparisons, indent=2))
    print(json.dumps(comparisons, indent=2))


if __name__ == "__main__":
    main()
