# 弗兰克-赫兹实验报告

在 `report/` 下运行：

```sh
python3 code/build.py
```

最终四页报告输出为 `report/report.pdf`，顶层只保留 `code/` 和该PDF。
第1、2页直接保留手写data PDF的预习、原始记录与教师签字；
第3、4页在原模板空白位置加入数据处理、结论、误差分析和三个讨论题答案。
不添加自动测量的观察或数据。

## 输入与计算

- `measurements.json`：两组各181点的原始电流、0.5 V电压步长、实验条件、峰搜索区间。
  电流按原记录保留nA；原始电压符号V与正文U的对应关系已明确定义。
- `assets/IMG_6338.jpg`：用户补充的氩管铭牌原图。铭牌推荐值为灯丝2.00 V、
  第一栅压2.10 V、拒斥电压7.20 V；实际第二组拒斥电压按记录为6.70 V。
- `analyze.py`：核验行数与电压连续性、重算全部峰位、逐差法、带截距线性回归及误差。
  每峰用实测最大值及左右各2点作二次拟合，平顶以首个最大值点为中心。
  逐差配对为(5,1)、(6,2)、(7,3)，每对相隔4个周期；线性回归使用全部7个峰。
  公认值11.7 V来自指导书印刷页122，不另取外部参考值。
- `transcribed.csv`、`results.json`：构建时更新的完整转录表和未舍入计算结果。
  CSV是生成结果，修改数据应编辑 `measurements.json`。
- `postlab.md`、`postlab.tex`：课后文字与LaTeX排版源；修改正文时同步更新二者。
- `弗兰克-赫兹实验_课后报告.md`：构建填入数值后的Markdown，图表渲染在临时目录完成。
- `assemble.py`：合并PDF、核对原前两页的内容流、尺寸及144 dpi逐像素一致性，
  并验证独立课后页与最终第3、4页渲染一致。
- `数据完整性核对.md`：原始资料、范围界定及转录核对说明，不属于提交正文。

原始输入为 `../../resource/实验10 弗兰克赫兹实验_data.pdf`，
空白模板为同目录 `_empty.pdf`，均不改写。
每次构建前后比较原始PDF的SHA-256，任何变化都会中止交付。
除报告源码、原始铭牌照片和计算结果外，曲线PDF、课后PDF、字体副本、
编译辅助文件及逐页渲染图均在系统临时目录生成并自动清理。

## 空白模板与检查

原来的 `main.tex`、`template.tex`、`fonts/`、`replicate.py`、
`prepare_fonts.py` 和 `validate.py` 保留，用于复刻空白模板。
`main.tex` 是空白模板入口，不是完整报告入口。

```sh
python3 code/build.py --template-only --qa-dir /tmp/fh-template-review
python3 code/build.py --qa-dir /tmp/fh-report-review
```

`--template-only` 不覆盖最终报告。`--qa-dir` 必须在 `report/` 之外；
它显式保留检查文件供逐页人工查看，检查后由调用者清理。
报告模式重点查看 `qa/report-1.png` 至 `qa/report-4.png`，
确认公式、中文、表格、图例、标题与页码无重叠。

## 依赖

需要 `latexmk`、XeLaTeX、Poppler `pdftoppm`。
正文使用TeX Live提供的Fandol、TeX Gyre Termes字体。
绘图默认使用 `/opt/miniconda3/envs/tf2/bin/python` 的NumPy、SciPy和Matplotlib；
PDF处理默认使用Codex bundled Python的pypdf、pdfplumber和Pillow；
空白模板字体准备使用tf2环境的fontTools。
可用 `--plot-python`、`--pdf-python`、`--font-python` 或
`PLOT_PYTHON`、`PDF_PYTHON`、`FONT_PYTHON` 覆盖默认路径。
