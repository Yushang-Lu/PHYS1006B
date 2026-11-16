import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="构建并拼接弗兰克-赫兹实验报告")
    parser.add_argument("--qa-dir", type=Path)
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument(
        "--plot-python",
        default=os.environ.get("PLOT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"),
    )
    parser.add_argument(
        "--pdf-python",
        default=os.environ.get(
            "PDF_PYTHON",
            str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
        ),
    )
    parser.add_argument(
        "--font-python",
        default=os.environ.get("FONT_PYTHON", "/opt/miniconda3/envs/tf2/bin/python"),
    )
    arguments = parser.parse_args()
    if arguments.qa_dir:
        arguments.qa_dir = arguments.qa_dir.resolve()
        if arguments.qa_dir.is_relative_to(root.parent):
            parser.error("--qa-dir 必须位于 report/ 外，建议使用 /tmp/")
    resource = root.parent.parent / "resource"
    source = resource / "实验10 弗兰克赫兹实验_empty.pdf"
    hashes = {path: digest(path) for path in resource.glob("*.pdf")}
    with tempfile.TemporaryDirectory(prefix="phys1006b-fh-") as temporary:
        workspace = Path(temporary)
        for name in (
            "main.tex", "replicate.py", "prepare_fonts.py", "validate.py",
            "measurements.json", "analyze.py", "postlab.md", "postlab.tex", "assemble.py",
        ):
            shutil.copy2(root / name, workspace / name)
        has_template = (root / "template.tex").exists() and (root / "fonts").is_dir()
        if has_template:
            shutil.copy2(root / "template.tex", workspace / "template.tex")
            shutil.copytree(root / "fonts", workspace / "fonts")
        environment = os.environ.copy()
        environment["XDG_CACHE_HOME"] = str(workspace / "cache")
        environment["MPLCONFIGDIR"] = str(workspace / "mpl-cache")
        if arguments.template_only:
            commands = [] if has_template else [
                [arguments.pdf_python, "replicate.py", str(source)],
                [arguments.font_python, "prepare_fonts.py"],
            ]
            commands += [
                ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                [arguments.pdf_python, "validate.py", str(source), "main.pdf"],
            ]
            log_name = "main.log"
        else:
            records = resource / "实验10 弗兰克赫兹实验_data.pdf"
            commands = [
                [arguments.plot_python, "analyze.py"],
                ["latexmk", "-norc", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "postlab.tex"],
                [arguments.pdf_python, "assemble.py", str(records)],
            ]
            log_name = "postlab.log"
        for command in commands:
            subprocess.run(command, cwd=workspace, env=environment, check=True)
        log = (workspace / log_name).read_text()
        if "Missing character:" in log or "Overfull" in log:
            raise RuntimeError("排版检查失败：缺字或溢出。")
        if any(digest(path) != previous for path, previous in hashes.items()):
            raise RuntimeError("原始 PDF 被意外修改。")
        if arguments.template_only and not has_template:
            shutil.copy2(workspace / "template.tex", root / "template.tex")
            shutil.copytree(workspace / "fonts", root / "fonts", dirs_exist_ok=True)
        if arguments.qa_dir:
            arguments.qa_dir.mkdir(parents=True, exist_ok=True)
            for name in (
                "main.tex", "template.tex", "main.pdf", "main.log", "qa.json",
                "postlab.tex", "postlab.pdf", "postlab-rendered.pdf", "postlab.log",
                "report.pdf", "curves.pdf", "numbers.tex", "results.json", "report.md",
            ):
                if (workspace / name).exists():
                    shutil.copy2(workspace / name, arguments.qa_dir / name)
            shutil.copytree(workspace / "qa", arguments.qa_dir / "qa", dirs_exist_ok=True)
        if arguments.template_only:
            print("空白模板检查完成；未覆盖最终报告。")
            return
        for name in ("results.json", "transcribed.csv"):
            shutil.copy2(workspace / name, root / name)
        shutil.copy2(workspace / "report.md", root / "弗兰克-赫兹实验_课后报告.md")
        descriptor, staging = tempfile.mkstemp(prefix=".report-", dir=root.parent)
        os.close(descriptor)
        try:
            shutil.copyfile(workspace / "report.pdf", staging)
            os.replace(staging, root.parent / "report.pdf")
        finally:
            Path(staging).unlink(missing_ok=True)
    print(f"完整报告：{root.parent / 'report.pdf'}")


if __name__ == "__main__":
    main()
