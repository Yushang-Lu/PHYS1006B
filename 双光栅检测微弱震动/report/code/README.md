# 双光栅实验报告

在本实验的 `report/` 下运行：

```sh
python3 code/build.py
```

输出三页拼接报告 `report.pdf`：前两页保留data PDF的预习、原始记录与签字；
第三页在LaTeX复刻模板上填写数据处理、结论、误差分析和讨论题。
原始 `resource/实验4 双光栅检测微弱振动_empty.pdf` 和 `_data.pdf` 不改写；
构建前后校验其SHA-256。

## 源码

- `measurements.json`：用户确认后的原始输入，第五个扫频点为503.840 Hz。
- `analyze.py`：Decimal计算振幅，生成数值、表格、九点折线和Markdown；
  `results.json` 为构建生成结果，修改数据应编辑输入文件。
- `postlab.md`、`postlab.tex`：正文与LaTeX源，修改正文时同步更新。
- `双光栅检测微弱振动_课后报告.md`：构建填入计算结果的正文。
  图引用 `curve.pdf`，该矢量图在临时构建目录生成并嵌入最终PDF，不额外留存。
- `assemble.py`：调用physics-lab-report技能的拼接脚本，
  核验前两页内容流、尺寸及144 dpi像素完全一致，独立课后页与最终第三页一致。
  检查结果保存为 `report-validation.json`。

- `main.tex`：XeLaTeX入口、纸张尺寸和字体定义。
- `template.tex`：逐字符和逐线条的LaTeX排版，可编辑；首次构建从原模板生成。
- `fonts/`：从原模板提取的嵌入字体子集，仅覆盖模板已有字符。
  后续填写新文字应另用完整中文字体。
- `replicate.py`、`prepare_fonts.py`：首次构建提取文字坐标、表格线及字体，
  补全字体所需表；不是将整页PDF或截图作为底图。
- `validate.py`：核对三页的尺寸、非空白字符计数、无位图，
  并以144 dpi逐页渲染原件与复刻件进行像素差异检查。
- `validation.json`：最近一次构建的逐页像素平均绝对差，范围0–255；
  不代表逐像素完全相同。
- `数据完整性核对.md`：原数据转录、指导书依据和待确认项，不进入空白PDF。

复刻保留原模板的标题、表格、留白、页码，以及首页“总成绩”下划线换行等原有布局。
`template.tex` 和字体存在时构建直接使用，保留后续人工排版修改。

## 依赖与检查

需要Python 3.9+、XeLaTeX、latexmk、Poppler `pdftoppm`。
PDF脚本需要pdfplumber、pypdf、Pillow；字体脚本需要fontTools。
绘图需要Matplotlib，默认使用conda `tf2`，可通过 `PLOT_PYTHON` 或
`--plot-python` 指定；拼接脚本需要reportlab。
默认分别使用Codex bundled Python和conda `tf2` Python；
可通过 `PDF_PYTHON`、`FONT_PYTHON` 或 `--pdf-python`、`--font-python` 指定。

所有编译产物和渲染图默认在系统临时目录生成并自动清理。
人工逐页对照时可显式导出到 `report/` 外：

```sh
python3 code/build.py --qa-dir /tmp/grating-template-qa
```

查看 `qa/report-1.png` 至 `qa/report-3.png`，以及
`qa/compare-1.png` 至 `qa/compare-3.png`（左空白原件、右复刻），
检查完成后清理该临时目录。`report/` 顶层仅保留 `code/` 和 `report.pdf`。

仅检查空白复刻可运行 `python3 code/build.py --template-only`，不会覆盖完整报告。
独立课后PDF、拼接用分拆PDF、图表和编译文件均在临时目录生成并自动清理。
