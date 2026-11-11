import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument("--qa-dir", type=Path)
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
    source = root.parent.parent / "resource/实验6 太阳能电池的基本特性研究_20260915092644.pdf"
    if arguments.qa_dir and arguments.qa_dir.resolve().is_relative_to(root.parent):
        parser.error("--qa-dir must be outside report/")
    with tempfile.TemporaryDirectory(prefix="phys1006b-solar-") as temporary:
        workspace = Path(temporary)
        shutil.copytree(root, workspace, dirs_exist_ok=True)
        environment = os.environ.copy()
        environment["MPLCONFIGDIR"] = str(workspace / "mpl-cache")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        def run(command):
            subprocess.run(command, cwd=workspace, env=environment, check=True)

        def compile_tex(name):
            run(["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", name])

        run([arguments.pdf_python, "replicate.py", str(source), "main.tex"])
        compile_tex("main.tex")
        if not arguments.template_only:
            run([arguments.plot_python, "analyze.py"])
            compile_tex("record-additions.tex")
            compile_tex("postlab.tex")
            run([arguments.pdf_python, "assemble.py"])
            destination = root.parent / "report.pdf"
            descriptor, staged = tempfile.mkstemp(prefix=".report-", dir=root.parent)
            os.close(descriptor)
            try:
                shutil.copyfile(workspace / "report.pdf", staged)
                os.replace(staged, destination)
            finally:
                Path(staged).unlink(missing_ok=True)
            print(f"完成：{destination}")
        if arguments.qa_dir:
            arguments.qa_dir.mkdir(parents=True, exist_ok=True)
            for name in (
                "main.tex", "main.pdf", "postlab.pdf", "report.pdf",
                "results.json", "powers.csv", "analysis.md", "curves.pdf",
            ):
                if (workspace / name).exists():
                    shutil.copy2(workspace / name, arguments.qa_dir / name)


if __name__ == "__main__":
    main()
