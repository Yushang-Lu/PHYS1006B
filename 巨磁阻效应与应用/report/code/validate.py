import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageChops
from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    workspace = Path("qa")
    workspace.mkdir()
    for document, prefix, extra in (
        (arguments.source, "original", ["-f", "1", "-l", "4"]),
        (Path("report.pdf"), "page", []),
        (Path("postlab.pdf"), "postlab", []),
    ):
        subprocess.run(
            ["pdftoppm", "-scale-to", "1500", "-png", *extra, str(document), str(workspace / prefix)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
    for page in range(1, 5):
        with Image.open(workspace / f"original-{page}.png") as original:
            with Image.open(workspace / f"page-{page}.png") as result:
                if original.size != result.size or ImageChops.difference(
                    original.convert("RGB"), result.convert("RGB")
                ).getbbox() is not None:
                    raise ValueError(f"Preserved page {page} pixels changed")
    final = PdfReader("report.pdf")
    postlab = PdfReader("postlab.pdf")
    if len(final.pages) != 4 + len(postlab.pages):
        raise ValueError("Incorrect page assembly")
    for index, page in enumerate(postlab.pages):
        text = page.extract_text()
        if "@@" in text or str(index + 5) not in text:
            raise ValueError("Unresolved placeholder or missing page number")
        if page.get_contents().get_data() != final.pages[index + 4].get_contents().get_data():
            raise ValueError("Postlab content changed during assembly")
    log = Path("postlab.log").read_text(encoding="utf-8")
    for problem in ("Missing character:", "Overfull", "LaTeX Warning:", "LaTeX Font Warning:"):
        if problem in log:
            raise ValueError(f"Inspect compilation diagnostics: {problem}")
    (workspace / "checks.json").write_text(json.dumps({
        "pages": len(final.pages),
        "preserved_pages_pixel_identical": [1, 2, 3, 4],
        "postlab_pages": len(postlab.pages),
        "postlab_content_streams_identical": True,
        "manual_visual_review_required": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
