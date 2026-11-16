import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

import pdfplumber
from PIL import Image, ImageChops, ImageStat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("replica", type=Path)
    arguments = parser.parse_args()
    with pdfplumber.open(arguments.source) as original, pdfplumber.open(arguments.replica) as replica:
        if len(original.pages) != 4 or len(replica.pages) != 4:
            raise ValueError("模板必须恰为四页")
        for before, after in zip(original.pages, replica.pages):
            if abs(before.width - after.width) > 0.02 or abs(before.height - after.height) > 0.02:
                raise ValueError("页面尺寸不一致")
            before_text = Counter(character["text"] for character in before.chars if character["text"].strip())
            after_text = Counter(character["text"] for character in after.chars if character["text"].strip())
            if before_text != after_text:
                raise ValueError(f"第 {before.page_number} 页文字不一致：{before_text - after_text}, {after_text - before_text}")
            if after.images:
                raise ValueError("复刻中不得使用整页截图")
    Path("qa").mkdir(exist_ok=True)
    for label, path in (("original", arguments.source), ("replica", arguments.replica)):
        subprocess.run(["pdftoppm", "-r", "144", "-png", str(path), f"qa/{label}"], check=True)
    metrics = []
    for number in range(1, 5):
        before = Image.open(f"qa/original-{number}.png").convert("RGB")
        after = Image.open(f"qa/replica-{number}.png").convert("RGB")
        difference = ImageChops.difference(before, after)
        average = sum(ImageStat.Stat(difference).mean) / 3
        metrics.append({"page": number, "mean_absolute_channel_error_0_255": average})
        if average > 3:
            raise ValueError(f"第 {number} 页渲染差异过大：{average:.4f}")
        comparison = Image.new("RGB", (before.width * 2, before.height), "white")
        comparison.paste(before, (0, 0))
        comparison.paste(after, (before.width, 0))
        comparison.save(f"qa/compare-{number}.png")
    Path("qa.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
