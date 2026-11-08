from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="重建 report/report.pdf，自动清理中间文件。")
    parser.add_argument(
        "--plot-python",
        default=os.environ.get("PLOT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"),
    )
    parser.add_argument(
        "--pdf-python",
        default=os.environ.get(
            "PDF_PYTHON",
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python"),
        ),
    )
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="phys1006b-report-") as temporary:
        workspace = Path(temporary)
        for name in ("main.tex", "postlab.tex", "analyze.py", "assemble.py"):
            shutil.copy2(root / name, workspace / name)
        shutil.copytree(root / "assets", workspace / "assets")
        environment = os.environ.copy()
        environment["MPLCONFIGDIR"] = str(workspace / "matplotlib-cache")
        commands = [
            [arguments.plot_python, "analyze.py"],
            ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
            ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "postlab.tex"],
            [arguments.pdf_python, "assemble.py", "--output", str(workspace / "report.pdf")],
        ]
        for command in commands:
            subprocess.run(command, cwd=workspace, env=environment, check=True)
        destination = root.parent / "report.pdf"
        descriptor, staged_path = tempfile.mkstemp(prefix=".report-", dir=root.parent)
        os.close(descriptor)
        try:
            shutil.copyfile(workspace / "report.pdf", staged_path)
            os.replace(staged_path, destination)
        finally:
            if os.path.exists(staged_path):
                os.unlink(staged_path)
    print(f"完成：{destination}")


if __name__ == "__main__":
    main()
