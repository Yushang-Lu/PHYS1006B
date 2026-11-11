# 太阳能电池的基本特性研究：报告构建

在本实验的 `report/` 下运行：

```sh
python3 code/build.py
```

最终仅更新 `report/report.pdf`。计算、绘图、模板重绘、LaTeX 编译和 PDF 合并
均在系统临时目录进行，退出时自动清理；失败不覆盖已有成品。
不修改 `resource/` 的空白模板、原始记录 PDF 或其他实验。

## 文件

- `assets/原始记录.pdf`：用户 Downloads 中附件的完整原始副本。
- `assets/教师签名.png`：用户提供的签名照片原样副本。
- `assets/measurements.json`：第2、3页数据转录，保留电压、电流符号与单位。
- `replicate.py`：提取空白模板逐字基线、字体、字号、描边粗细及表格线，
  生成五页 `main.tex`；不用原 PDF 或截图作模板背景。
- `layout.tex`：页面尺寸、字体和绝对定位命令。
- `analyze.py`：计算所有输出功率、最大功率点、最佳负载、填充因子和效率，
  生成曲线、结果表、功率表及已填数值 Markdown。
- `postlab.tex`：第4、5页正文；`postlab.md` 是对应 Markdown 文本模板。
- `record-additions.tex`：第3页下方的功率计算表和手写“3”下方的签名照片。
- `assemble.py`：原样复制附件前2页，第3页仅叠加上述内容，
  再合入复原模板和课后正文。
- `check.py`：渲染逐页检查图和模板对照图，比较保留页与原附件的像素。
- `build.py`：统一构建入口。

## 数据处理口径

指导书为根目录《大学物理实验B指导书0903.pdf》印刷页71–78。
原记录将“单晶硅”用红字改为“多晶硅”；空白模板照原文复原，
分析、图例及结论采用实际记录中的多晶硅。

表1两种电池各18点；表2每种电池各8组开路电压及短路电流；
表3多晶硅13点，非晶硅14点。多晶硅最后一组为
`2.24 V, 0.223 mA`，非晶硅最后一组为 `2.43 V, 0.239 mA`。
表2第二档光强为 `434 W/m²`；表3光强为 `102.9 W/m²`。
面积依模板取 `50 mm × 50 mm = 0.0025 m²`。

曲线用线段连接实测点，不拟造原点或开路点；暗态反向区另作同数据放大图。
最大功率采用实测点中最大的 `V × I`，最佳负载为该点的 `V/I`；
报告明确它是离散实测最大点估计。
`FF = Pmax/(VOC ISC)` 中短路电流取表3零电压点；
开路电压取表2同光强、40 cm处的实测值 `2.25 V, 2.46 V`，
不将表3有限负载下的末点冒充开路点，不作开路电压外推。
表3功率列原本空白，依用户修订要求，在第3页原记录下方另列完整功率表，
第5页不再重复。签名照片等比例置于第3页手写“3”下方，不遮挡原记录。

修改测量值或常数后重新构建，结果、公式数值、表格、曲线和 Markdown 同步生成。
定性结论和误差分析仍应随修改后的数据复核。

## 复原与交付检查

本次先单独编译、检查五页空白模板，再编写正文。
重建检查产物：

```sh
python3 code/build.py --template-only --qa-dir /tmp/solar-template-check
python3 code/build.py --qa-dir /tmp/solar-report-check
/Users/jinana/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python code/check.py /tmp/solar-report-check
```

`--qa-dir` 必须位于 `report/` 之外。它仅为人工检查导出模板、课后 PDF、
最终 PDF、曲线、计算结果、功率 CSV 和 Markdown；普通构建不留这些中间产物。
检查目录请放在 `/tmp`，无需保存到仓库。
`check.py` 对前2页及课后页做逐像素相等断言，并检查第3页新增区域外
像素不变；`assemble.py` 也断言前2页页面内容流未变。
最终前3页保留附件自己的纸张尺寸，后2页按空白模板尺寸重绘。

## 依赖

- 系统 Python 3.9+ 运行统一构建入口。
- XeLaTeX、latexmk（本机 TeX Live）。
- conda `tf2` Python：NumPy、Matplotlib。
- Codex runtime Python 3.10+：pdfplumber、pypdf、Pillow。
- WPS 字体缓存中的汉仪字体，系统 Times New Roman，
  WPS 应用内的 `KingsoftSign.ttf`；完整字体路径见 `layout.tex`。
- Poppler `pdftoppm` 用于视觉检查。

Python 路径可用 `--plot-python`、`--pdf-python` 或环境变量
`PLOT_PYTHON`、`PDF_PYTHON` 覆盖。
WPS 符号字体没有普通空格，XeLaTeX 选择该字体时可能报告 U+0020 提示；
模板中的 η 和等号均正常绘制。不能仅凭编译成功代替最终视觉检查。
