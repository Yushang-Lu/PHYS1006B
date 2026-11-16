from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot-python", default=os.environ.get("PLOT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"))
    parser.add_argument(
        "--pdf-python",
        default=os.environ.get(
            "PDF_PYTHON",
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
        ),
    )
    arguments = parser.parse_args()
    measurements = json.loads((root / "measurements.json").read_text())
    source = (root / measurements["source"]).resolve()
    with tempfile.TemporaryDirectory(prefix="electron-em-") as temporary:
        workspace = Path(temporary)
        for name in ("measurements.json", "analyze.py", "assemble.py", "postlab.tex", "postlab.md"):
            shutil.copy2(root / name, workspace / name)
        environment = os.environ.copy()
        environment["MPLCONFIGDIR"] = str(workspace / "mpl-cache")
        environment["XDG_CACHE_HOME"] = str(workspace / "cache")
        commands = [
            [arguments.plot_python, "analyze.py"],
            ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "postlab.tex"],
            [arguments.pdf_python, "assemble.py", str(source)],
        ]
        for command in commands:
            subprocess.run(command, cwd=workspace, env=environment, check=True)
        log = (workspace / "postlab.log").read_text()
        if "Missing character:" in log or "Overfull" in log:
            raise RuntimeError("排版检查失败：缺字或内容溢出。")
        shutil.copy2(workspace / "results.json", root / "results.json")
        shutil.copy2(workspace / "rendered.md", root / "电子荷质比的测定_课后报告.md")
        descriptor, staging = tempfile.mkstemp(prefix=".report-", dir=root.parent)
        os.close(descriptor)
        try:
            shutil.copyfile(workspace / "report.pdf", staging)
            os.replace(staging, root.parent / "report.pdf")
        finally:
            if os.path.exists(staging):
                os.unlink(staging)
    print(f"完成：{root.parent / 'report.pdf'}")


if __name__ == "__main__":
    main()
