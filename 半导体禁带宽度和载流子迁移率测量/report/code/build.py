import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-dir", type=Path)
    parser.add_argument("--plot-python", default=os.environ.get("PLOT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"))
    parser.add_argument(
        "--pdf-python",
        default=os.environ.get(
            "PDF_PYTHON",
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
        ),
    )
    arguments = parser.parse_args()
    if arguments.qa_dir and arguments.qa_dir.resolve().is_relative_to(root.parent):
        parser.error("--qa-dir must be outside report/")
    data = json.loads((root / "measurements.json").read_text())
    source = (root / data["source"]).resolve()
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="phys1006b-semiconductor-") as temporary:
        workspace = Path(temporary)
        shutil.copytree(root, workspace, dirs_exist_ok=True)
        environment = os.environ.copy()
        environment["MPLCONFIGDIR"] = str(workspace / "mpl-cache")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        def run(command):
            subprocess.run(command, cwd=workspace, env=environment, check=True)

        run([arguments.plot_python, "analyze.py"])
        run(["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "postlab.tex"])
        run([arguments.pdf_python, "assemble.py", str(source), str(workspace)])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
        if arguments.qa_dir:
            arguments.qa_dir.mkdir(parents=True, exist_ok=True)
            for name in (
                "report.pdf", "postlab.pdf", "analysis.md", "results.json",
                "transcription_audit.json", "verification.json", "hall.pdf", "gap.pdf",
            ):
                shutil.copy2(workspace / name, arguments.qa_dir / name)
            for image in workspace.glob("final-*.png"):
                shutil.copy2(image, arguments.qa_dir / image.name)
        destination = root.parent / "report.pdf"
        descriptor, staged = tempfile.mkstemp(prefix=".report-", dir=root.parent)
        os.close(descriptor)
        try:
            shutil.copyfile(workspace / "report.pdf", staged)
            os.replace(staged, destination)
        finally:
            Path(staged).unlink(missing_ok=True)
        print(f"完成：{destination}")


if __name__ == "__main__":
    main()
