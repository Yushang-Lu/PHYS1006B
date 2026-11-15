# 巨磁阻效应与应用：报告构建

`report.pdf` 为拼接后的实验报告：前四页直接保留新版手填PDF，
从第5页起接入计算、曲线、结论、误差分析及讨论题。原始PDF不修改。

## 构建

在本实验的 `report/` 下运行：

```sh
python3 code/build.py
```

构建生成 `report/report.pdf` 和填入数值的 `report/code/report.md`。
绘图、数据换算、LaTeX编译、PDF合并及页面渲染均在系统临时目录完成，退出时清理。
先校验手填版SHA-256与转录版本一致，再校验前四页合并后的内容流及渲染像素完全不变。
构建失败不覆盖已有成品。替换原始PDF后，须重新核对数据并更新 `source_sha256`。

如需检查生成的LaTeX或渲染PDF：

```sh
python3 code/build.py --qa-dir /tmp/gmr-report-check
```

检查目录导出课后PDF、合并PDF、图表、数值结果、换算CSV及逐页渲染。
`--qa-dir` 仅允许在 `report/` 外，由调用者检查后删除。

原六页空白模板仍可复现，不覆盖最终报告：

```sh
python3 code/build.py --template-only --qa-dir /tmp/gmr-template-check
```

## 源文件

- `measurements.json`：六项实验的数据、常数、来源页码及版本哈希。
- `analyze.py`：换算、直线拟合、绘图及将限定格式的Markdown转换为LaTeX正文。
- `postlab.md`：正文模板，`@@名称@@` 数值由计算替换；`report.md` 为生成的可读正文。
- `postlab.tex`：课后页的中文字体、页眉、页码、表格与公式样式。
- `assemble.py`：保留手填版前四页，拼接课后页并添加书签。
- `validate.py`：逐页渲染、前四页像素比较、内容流及编译诊断检查。
- `replicate.py`、`prepare_fonts.py`、`layout.tex`：独立的空白模板复现工具。
- `build.py`：统一构建入口；`QA.md` 记录核对过程和需要用户补充的原始量。

## 依赖及口径

使用本机 `latexmk`、XeLaTeX；PDF提取使用包含 `pdfplumber`、`pypdf` 的Python，
默认采用 Codex bundled runtime，可用 `PDF_PYTHON` 或 `--pdf-python` 覆盖。
绘图使用 conda `tf2` 的NumPy、Matplotlib，可用 `PLOT_PYTHON` 或 `--plot-python` 覆盖。
检查依赖Poppler及Pillow；正文使用TeX Live自带Fandol及TeX Gyre Termes完整字体。
空白模板模式另使用 `fontTools`，可用 `FONT_PYTHON` 或 `--font-python` 指定Python。
此模式提取原模板内嵌字体并补全OS/2、post元数据，不改字形轮廓。
不访问WPS缓存，不将字体副本纳入仓库；字体缓存及图表缓存均置于临时目录。

指导书为根目录《大学物理实验B指导书0903.pdf》实验五，印刷页49–68。
按指导书给出的 μ₀＝4π×10⁻⁷ H/m、n＝24000 匝/m、供电4 V计算，
B/Gauss＝0.3015928947×(I_M/mA)，R/Ω＝4000/(I_R/mA)。
R采用指导书的端口等效电阻口径，不换算成单个桥臂阻值。
所有实测曲线保留数据点，并按记录顺序作折线，不用平滑拟合替代原始点。
电流测量的四组灵敏度由所有七点的最小二乘直线斜率给出，单位mV/mA。
表5原角度坐标保留，不把0°处的49.7 mV改为零，不移动起点。
表6按区域1为最高位；读出电压按两组电平间的最大间隙分类，复核写入码。
该分类边界不是表3开关器件的实测阈值。

## 数据状态

当前输入为 `resource/实验5 巨磁阻效应与应用_data.pdf`。
表3的高、低电平仍为空白，`measurements.json` 对应字段为 `null`；
开关图仅以低、高电平表示输出状态，不给出虚构电压，也不借用表6的读数。
用户提供这两个实测值后可填入对应字段，重建时自动使用实际电压纵轴。
表6的十进制空格仍在原始页保留，结果203列于课后数据处理。

本次电流数据的适当偏置灵敏度小于低偏置，正文按实际结果解释，不照搬理想趋势。
常数或输入改变后应统一构建，并复核全部结论、比较和文字，尤其是灵敏度大小关系。
