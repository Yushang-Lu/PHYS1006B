# 报告源码与构建

在 `report` 目录执行：

```sh
python3 code/build.py
```

也可在任意目录使用 `build.py` 的绝对路径。最终仅输出 `report/report.pdf`。
图表、计算结果、模板 PDF、课后报告 PDF 和 LaTeX 辅助文件均在系统临时目录生成，
构建结束自动删除。构建失败不覆盖已有成品。

## 源码

- `main.tex`：原四页空白模板，内容保持不变。
- `postlab.tex`：第三、四页的正文及排版。
- `assets/measurements.json`：原始测量值与计算常数。
- `analyze.py`：计算、拟合与绘图。
- `assemble.py`：原样复制模板前两页，接入完成后的第三、四页。
- `build.py`：统一构建入口，请通过此入口生成报告。

默认用 conda `tf2` 的 Python 计算绘图，用已安装 `pypdf` 的 Codex Python 合并 PDF。
可通过 `--plot-python`、`--pdf-python` 参数或 `PLOT_PYTHON`、`PDF_PYTHON` 环境变量替换。
另需 `latexmk`、XeLaTeX，以及 TeX 源码指定的本机 WPS 汉仪字体和 Times New Roman。

数据处理保留原始负电压，以其大小计算。电荷值采用指导书的
`1.602e-19 C`，比较值为 `6.626e-34 J·s`。
最小二乘法使用全部五点；作图法仍用高低频各两点的平均点连线。
