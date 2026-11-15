import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="构建并拼接巨磁阻效应实验报告")
    parser.add_argument("--qa-dir", type=Path)
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument(
        "--plot-python",
        default=os.environ.get("PLOT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"),
    )
    parser.add_argument(
        "--font-python",
        default=os.environ.get("FONT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"),
    )
    parser.add_argument(
        "--pdf-python",
        default=os.environ.get(
            "PDF_PYTHON",
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
        ),
    )
    arguments = parser.parse_args()
    if arguments.qa_dir:
        arguments.qa_dir = arguments.qa_dir.resolve()
        if arguments.qa_dir.is_relative_to(root.parent):
            parser.error("--qa-dir 必须位于 report/ 之外，建议使用 /tmp/")
    sources = sorted((root.parent.parent / "resource").glob("*.pdf"))
    hashes = {source: digest(source) for source in sources}
    source = root.parent.parent / "resource/实验5 巨磁阻效应与应用_20260920220557.pdf"
    data = json.loads((root / "measurements.json").read_text(encoding="utf-8"))
    records = (root / data["source"]).resolve()
    if not arguments.template_only and digest(records) != data["source_sha256"]:
        raise ValueError("手填PDF已变化：请重新核对转录数据并更新source_sha256")
    with tempfile.TemporaryDirectory(prefix="phys1006b-gmr-") as temporary:
        workspace = Path(temporary)
        shutil.copytree(root, workspace, dirs_exist_ok=True)
        environment = os.environ.copy()
        environment["MPLCONFIGDIR"] = str(workspace / "mpl-cache")
        environment["XDG_CACHE_HOME"] = str(workspace / "cache")

        def run(command):
            subprocess.run(command, cwd=workspace, env=environment, check=True)

        if arguments.template_only:
            run([arguments.pdf_python, "replicate.py", str(source), "main.tex"])
            run([arguments.font_python, "prepare_fonts.py"])
            run(["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
        else:
            run([arguments.plot_python, "analyze.py"])
            run(["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "postlab.tex"])
            run([arguments.pdf_python, "assemble.py", str(records)])
            run([arguments.pdf_python, "validate.py", str(records)])
        if any(digest(path) != previous for path, previous in hashes.items()):
            raise ValueError("Source PDF changed during build")
        if arguments.qa_dir:
            arguments.qa_dir.mkdir(parents=True, exist_ok=True)
            for name in (
                "main.tex", "main.pdf", "main.log", "postlab.pdf", "postlab.log",
                "report.pdf", "report.md", "body.tex", "results.json", "converted.csv",
                "characteristics.pdf", "switch.pdf", "current.pdf", "angle.pdf",
            ):
                if (workspace / name).exists():
                    shutil.copy2(workspace / name, arguments.qa_dir / name)
            if (workspace / "qa").exists():
                shutil.copytree(workspace / "qa", arguments.qa_dir / "qa", dirs_exist_ok=True)
        if arguments.template_only:
            print("空白模板构建完成；未覆盖最终报告。使用 --qa-dir 导出检查文件。")
            return
        descriptor, staged = tempfile.mkstemp(prefix=".report-", dir=root.parent)
        os.close(descriptor)
        try:
            shutil.copyfile(workspace / "report.pdf", staged)
            os.replace(staged, root.parent / "report.pdf")
        finally:
            Path(staged).unlink(missing_ok=True)
        shutil.copyfile(workspace / "report.md", root / "report.md")
    print(f"完整报告：{root.parent / 'report.pdf'}")


if __name__ == "__main__":
    main()
