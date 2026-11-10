# 用示波器观测磁滞回线：报告构建

在本实验的 `report/` 下运行：

```sh
python3 code/build.py
```

只更新 `report/report.pdf`。计算、绘图、LaTeX 编译和 PDF 合并均在系统临时目录完成，
退出时自动清理；构建失败不覆盖已有成品。不修改 `resource/` 中的原模板及上次实验。

## 文件

- `replicate.py`：从原模板提取文字基线、字体、字号、表格线，生成逐字定位的 `main.tex`；
  原模板四页均由 XeLaTeX 重绘，不以原 PDF 或截图充当模板背景。
- `layout.tex`：页面尺寸、原模板字体与绝对定位工具。
- `assets/原始记录.png`：用户提供的手写记录原图，未修改像素。
- `assets/measurements.json`：带单位的电压转录、元件参数、样品几何参数及来源。
- `analyze.py`：电压换算、逐段线性插值、绘图和表格生成。
- `postlab.tex`：第三、四页正文；`postlab.md` 为对应 Markdown 内容模板，
  数值占位符在构建时替换成 `analysis.md`。
- `assemble.py`：第一页直接保留原模板；第二页保留页眉、节标题、签字栏和页码，
  将用户的完整手写记录图置于数据区；第三、四页使用 LaTeX 复原模板并填入正文。
- `build.py`：统一构建入口。

## 依赖

- `latexmk`、XeLaTeX（本机 TeX Live）。
- conda `tf2` Python：NumPy、Matplotlib、Pillow。
- Codex runtime Python：pdfplumber、pypdf、ReportLab、Pillow。
- 本机 WPS 字体缓存内的汉仪书宋二、汉仪中黑、汉仪楷体、汉仪中等线；
  系统 Times New Roman。字体路径见 `layout.tex`。
- 视觉检查使用系统 Poppler 的 `pdftoppm`。

Python 路径可用 `--plot-python`、`--pdf-python` 或 `PLOT_PYTHON`、`PDF_PYTHON` 覆盖。

## 复原与检查

本次先单独编译、检查四页空白模板，再编写报告正文。可复现：

```sh
python3 code/build.py --template-only --qa-dir /tmp/hysteresis-template-check
python3 code/build.py --qa-dir /tmp/hysteresis-report-check
```

`--qa-dir` 仅供检查；请使用报告目录以外的临时路径。该选项导出中间模板、
课后 PDF、最终 PDF、计算结果、换算数据 CSV、已填数值 Markdown。
不加此选项时，所有中间产物自动清理。

## 数据处理口径

指导书采用印刷页 31–36 的“实验三”，样品参数来自第 35 页。
两样品各有 20 个 40 Hz 回线坐标、10 个基本磁化曲线顶点。
基本磁化曲线的首点纵坐标分别为原图的 600 μV 和 400 μV，
存储时换算为 0.600 mV、0.400 mV；其余电压均按 mV 保存，保留正负号。
原图样品2基本磁化曲线第 11–20 列为空，不作为数据使用。

按测量顺序用折线连接全部实测点；回线末点连接首点，基本磁化曲线不增添原点。
在跨轴相邻测点之间作线性插值，分别求正负支剩磁和矫顽力，
以两支绝对值的算术平均值报告其大小。插值通式：

```text
y(0) = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
```

几何常数、元件参数或电压改动后重新运行构建，换算系数、结果表和图同步更新。
结论及讨论中的比较、分类文字须结合新结果复核。
指导书操作部分另有样品2的 100 Hz 测量；本次图片只有 40 Hz，
因此本报告依报告要求绘制两种样品在所给频率下的回线和基本磁化曲线，不扩展频率比较。

## 页面保留

第一页预习内容、身份信息仍为空白，未代填；第一页内容流在合并时做相等断言。
手写记录以原图无损嵌入，原图保存在输入目录，正文不重写原始读数。
复原模板的“基本磁滞回线”原字样不改；记录图中用户已更正的红字原样保留，
正文采用指导书的“基本磁化曲线”名称。
