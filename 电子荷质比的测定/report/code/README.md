# 电子荷质比报告构建

在 `report/` 目录运行 `python3 code/build.py`。只在 `report/` 顶层输出 `report.pdf`。
计算、拟合图、课后报告 PDF、拼接及像素比较均在系统临时目录完成，结束自动清理。

## 输入与源码

- `measurements.json`：新版 data PDF 的原始读数、实验常数，以及单独标识的假设半径。
- `analyze.py`：重算两种直接测量法、全九点带截距线性拟合、相对误差及图表。
- `postlab.md`：带计算占位符的课后报告 Markdown。
- `postlab.tex`：与 Markdown 对应的第4、5页正文排版；修改正文时同步修改 Markdown。
- `assemble.py`：保留新版 data PDF 前三页，在第4、5页空白位置叠加正文；前三页逐页进行100 dpi像素比较。
- `results.json`、`电子荷质比的测定_课后报告.md`：构建时自动更新的计算结果和填入数值后的 Markdown。

原始输入引用 `../../resource/实验12 电子荷质比的测定_data.pdf`，不修改该文件。
手写的表格结果原样保留。全部计算使用未舍入数据，均值及误差最后舍入。
作图法的40 mm为假设半径，正文明确标注，不是实测记录，也不据此倒推、调整原始数据。
仪器精度没有来源，未设置虚构精度；正文仅给出不确定度传播关系，尚无完整数值不确定度。
因此该PDF是含明确假设试算的合并版，并非已核实全部实验条件的定稿。

## 依赖

需要 `latexmk`、XeLaTeX、Poppler `pdftoppm`，以及 Times New Roman、
WPS 缓存中的 `HYShuSongErKW.ttf` 和 `HYZhongHeiKW.ttf`（路径见 TeX 源码）。
绘图默认使用 `/opt/miniconda3/envs/tf2/bin/python` 的 NumPy、Matplotlib；
PDF处理默认使用 Codex bundled Python 的 pypdf。
可用 `--plot-python`、`--pdf-python` 或 `PLOT_PYTHON`、`PDF_PYTHON` 覆盖。

复核依据为指导书第138—144页、空白报告模板、新版 data PDF 及用户确认的实测初始直径。
线圈参数照片与指导书一致：N=132，R=158 mm，K≈7.51×10⁻⁴ T/A。
