---
name: 5writing
description: "数学建模竞赛论文撰写阶段，支持 Typst 和 LaTeX 双引擎。根据 ANALYSIS_MODELING_REPORT.md、RESULTS_REPORT.md 和 figures/*.pdf 选择比赛模板、排版引擎、组织章节，并在论文正文中按章节直接插入图表。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch
---

# 竞赛论文撰写（Typst / LaTeX）

本 skill 承接 `3coding-visual` 和 `4drawio`。前序阶段只提供真实数据、图表 PDF 和记录文件；本阶段负责选择比赛模板和排版引擎、组织论文结构，并决定每张图表放入哪个章节。

**Typst 引擎**下可调用 typst-author skill 学习 typst 写法；**LaTeX 引擎**参考本文件末尾的"LaTeX 写作要点"小节。

## 数学建模规范参考

如需领域判断，读取 `../_references/math_modeling_norms.md` 中的“论文写作”“图表与可视化”和“非数据图工具选择”小节。该文件只作为规范知识库，论文结构仍按比赛模板和当前赛题内容决定。

全国大学生数学建模竞赛（CUMCM）中文论文还必须读取 `../_references/cumcm_submission_rules.md`。该文件记录比赛特有的摘要页、目录、页码、正文页数、附录、支撑材料、匿名和 AI 工具声明要求；通用模板规则不得覆盖它。使用前核对规则年份和官方来源，发现当期官方通知变化时更新项目记录并按新规则执行。

## 模板族

本技能内捆绑的模板位于：

```text
templates/zh/<竞赛>/main.typ         # Typst 模板
templates/zh/<竞赛>-latex/main.tex   # LaTeX 模板
templates/en/<竞赛>/main.typ         # Typst 模板
templates/en/<竞赛>-latex/main.tex   # LaTeX 模板
```

**LaTeX 模板覆盖范围**：所有中文模板和英文模板均已提供 LaTeX 版本（`-latex` 后缀），使用 xelatex 编译。

支持的中文模板（Typst + LaTeX 双版本）：

```text
apmcm, changsanjiao, cumcm, default, diangongbei, dongsansheng,
huashubei, huaweibei, huazhongbei, mathorcup, mcm, shuweibei, stats, wuyibei
```

华为杯、华中杯、五一杯统一使用 `huaweibei`、`huazhongbei`、`wuyibei` 作为模板。

支持的英文模板（Typst + LaTeX 双版本）：

```text
apmcm, default, mcm
```

论文中的所有数值图表结论必须来自 `reports/RESULTS_REPORT.md` 或 `figures/*`。不得编造、估算或使用不同的四舍五入方式。

## CUMCM 2026 模板硬约束

选择 `zh/cumcm` 或 `zh/cumcm-latex` 时：

- 电子版论文第一页必须是含标题、中文摘要和关键词的摘要专用页；该页页码为 1，页脚居中。
- 摘要后直接进入正文，不生成目录或目录页；正文不超过 30 页，附录页数不限。
- 电子版不包含承诺书和编号专用页；纸质版所需的这两页由提交环节另行处理，不写入电子论文模板。
- 在参考文献之前生成“AI 工具使用声明”。声明必须反映实际使用情况；使用 AI 时还要在支撑材料中生成 `AI工具使用详情.pdf`。
- 附录必须包含支撑材料文件清单和完整可运行代码，或者按实际情况写明“本论文没有支撑材料”“本论文没有用到程序”。
- 摘要、正文、附录、支撑材料内容、文件名、目录名和文档属性不得泄露参赛者、学校或赛区身份。
- 复制模板后必须替换所有方括号占位说明；不得保留模板示例模型、示例假设或虚构数值。

这些要求属于 CUMCM 专用规则，不得扩展到其它竞赛模板。


## 工作流

### 步骤 0：读取并确定排版引擎

撰写前先读取当前会话和 `plan.md` 中的“用户偏好 → 排版引擎”。以用户最新的明确指示为准；会话中没有明确指示时，沿用 `plan.md` 的既有记录。

- 已有确定的引擎时直接使用，不再询问“是否沿用”，也不重复展示选择题。
- 只有引擎缺失且无法从现有材料确定，或记录存在无法根据用户最新指示消解的冲突时，才询问相关选项。
- 需要询问时，提供 LaTeX（推荐）和 Typst 两个选项。没有既有选择且用户跳过询问时，默认使用 LaTeX。
- 用户明确改选时，直接采用新引擎，并同步更新 `plan.md` 的相应偏好字段，保留其他计划内容。新确定或默认采用的引擎也要记录，默认值注明为默认选择。

根据确定的引擎选择对应模板族：

- **Typst 引擎**：使用 `templates/<lang>/<竞赛>/main.typ`，调用 typst-author skill。编译目录和参数见步骤 3 的“图片路径与编译目录”。
- **LaTeX 引擎**：使用 `templates/<lang>/<竞赛>-latex/main.tex`，xelatex 编译（中文和英文均需跑两遍解决交叉引用）。编译目录和参数见步骤 3 的“图片路径与编译目录”。

**后续步骤中的所有代码示例、文件扩展名、图片插入语法都必须按所选引擎选择对应版本，不要混用。**

### 步骤 1：选择语言和模板


沿用当前会话和 `plan.md` 中已确定的竞赛类型与论文语言，不重复询问。以用户最新的明确指示为准；会话中没有明确指示时，沿用 `plan.md` 的既有记录。语言均未确定时，MCM/ICM/COMAP 默认英文，其他默认中文。仅在竞赛类型缺失且无法从现有材料确定，或偏好记录存在无法消解的冲突时，询问相关项。将确定的竞赛类型和语言同步到 `plan.md` 的“用户偏好”记录，默认值注明为默认选择，保留其他计划内容。按确定的竞赛类型和语言选择模板。

模板键示例（Typst 引擎）：

```text
长三角 -> zh/changsanjiao
APMCM 英文版 -> en/apmcm
全国赛/国赛/CUMCM -> zh/cumcm
统计建模 -> zh/stats
MCM/ICM/COMAP -> en/mcm
```

模板键示例（LaTeX 引擎）：

```text
全国赛/国赛/CUMCM -> zh/cumcm-latex
MCM/ICM/COMAP -> en/mcm-latex
```

### 步骤 2：准备模板

用以下命令检查捆绑模板是否可访问（`SKILL_DIR` 为本 skill 所在目录）：

**Typst 模板**：

```bash
ls "$SKILL_DIR/templates/zh/<竞赛>/main.typ" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：直接将 `templates/zh/<竞赛>/` 整目录复制到 `paper/`。这些模板是自包含入口文件，不依赖额外共享样式文件。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 Typst 框架，并在 `paper/` 内注明"重建自 default 结构"。

存在匹配模板时，绝不从零开始写论文。

**LaTeX 模板**：

```bash
ls "$SKILL_DIR/templates/zh/<竞赛>-latex/main.tex" 2>/dev/null && echo "OK" || echo "MISSING"
```

- **文件存在（OK）**：将 `templates/zh/<竞赛>-latex/` 整目录复制到 `paper/`。
- **文件不存在（MISSING）**：说明 skill 未完整安装或在沙箱中，此时依照本 SKILL.md 步骤 3 列出的对应节文件结构，从零重建最小可编译 LaTeX 框架，并在 `paper/` 内注明"重建自 default-latex 结构"。


### 步骤 3：构建图表规划

在写正文各节之前，根据 `figures/*.pdf`、`reports/RESULTS_REPORT.md`，以及 `reports/DRAWIO_REPORT.md`（如果存在）构建图表规划：

```text
图表规划
fig_roadmap.pdf -> 引言/问题重述
fig_flow_q1.pdf -> 问题一模型构建
fig_flow_q2.pdf -> 问题二模型构建
fig_pipeline.pdf -> 数据预处理/方法节
结果图 -> 对应的结果节
```

#### 图片路径与编译目录

以下约定适用于项目根下并列放置 `paper/` 与 `figures/` 的布局：

| 引擎 | 图片代码所在位置 | 图片引用路径 |
| --- | --- | --- |
| Typst | `paper/main.typ` | `../figures/xxx.pdf` |
| Typst | `paper/sections/*.typ` | `../../figures/xxx.pdf` |
| LaTeX | `paper/main.tex` 或由它通过 `\input` / `\include` 引入的章节 | `../figures/xxx.pdf` |

Typst 的相对路径以调用处的 `.typ` 文件为基准。LaTeX 在本工作流中统一从入口文件所在目录编译，图片路径以该编译目录为基准，不能因为代码写在 `sections/` 中就增加一层 `../`。LaTeX 示例使用带扩展名的显式相对路径，并确认导言区加载了 `graphicx`；使用 `[H]` 时还需加载 `float`。

从 `paper/` 目录执行所选引擎对应的命令：

```bash
# Typst：将项目根设为 paper/ 的上级，使其能读取并列的 figures/
typst compile --root .. main.typ main.pdf
```

```bash
# LaTeX：两次均从 main.tex 所在目录执行
xelatex -halt-on-error -interaction=nonstopmode main.tex && xelatex -halt-on-error -interaction=nonstopmode main.tex
```

实际目录不同或入口文件不叫 `main` 时，按实际路径调整，记录项目根、入口文件、编译目录、命令和输出 PDF，交给 `6verity` 复用。Typst 的 `--root` 必须覆盖入口和引用资源。下列 Typst 插图示例写在 `paper/sections/*.typ`，LaTeX 示例可写在主文件或其章节中。

**Typst 引擎**图片插入：

```typst
#figure(
  image("../../figures/fig_q1_error_dist.pdf", width: 85%),
  caption: [问题一预测误差分布],
) <fig:q1-error>

如 @fig:q1-error 所示，……
```

**LaTeX 引擎**图片插入：

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../figures/fig_q1_error_dist.pdf}
  \caption{问题一预测误差分布}
  \label{fig:q1_error}
\end{figure}

如图~\ref{fig:q1_error}所示，……
```

英文论文使用英文图注。

### 步骤 4：撰写各节

**以下章节文件名按所选引擎使用 `.typ`（Typst）或 `.tex`（LaTeX）扩展名。** 例如 Typst 引擎用 `1_restatement.typ`，LaTeX 引擎用 `1_restatement.tex`。文件名主体保持一致。

中文数学建模通用模板各节文件（`changsanjiao`、`diangongbei`、`huashubei`、`mathorcup`、`wuyibei`）：

```text
1_restatement.typ  - 问题重述与分析
2_analysis.typ     - 数据理解与总体思路
3_assumptions.typ  - 模型假设
4_symbols.typ      - 符号说明
5_problem1.typ     - 问题一建模与求解
6_problem2.typ     - 问题二建模与求解
7_problem3.typ     - 问题三建模与求解
...         - 根据题目调整问题数量
8_evaluation.typ   - 灵敏度分析、模型评价与推广
A_code.typ         - 附录代码
```

国赛/华中杯/华为杯（`cumcm`、`huazhongbei`、`huaweibei`）按以下章节结构：

```text
1_restatement.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...        - 根据题目调整问题数量
8_sensitivity.typ
9_evaluation.typ
A_code.typ
```

其中 CUMCM 模板另有：

```text
10_conclusion.typ - 逐题结论与建议
A_appendix.typ    - 支撑材料清单和代码附录入口
```

`A_appendix.typ` 按实际情况引用 `A_code.typ`。华中杯和华为杯是否采用同一结论和附录结构，仍以各自当期模板和规则为准。

东三省模板（`dongsansheng`）额外使用单独摘要文件：

```text
abstract.typ
1_restatement.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...       - 根据题目调整问题数量
8_evaluation.typ
A_code.typ
```

数维杯模板（`shuweibei`）保留原 LaTeX 的示例入口命名：

```text
Abstract.typ
Introduction.typ
2_analysis.typ
3_assumptions.typ
4_symbols.typ
5_problem1.typ
6_problem2.typ
7_problem3.typ
...      - 根据题目调整问题数量
8_evaluation.typ
Appendices1.typ
A_code.typ
```

中文默认模板（`default`）：

```text
1_restatement.typ
2_assumptions.typ
3_symbols.typ
4_problem1.typ
5_problem2.typ
6_problem3.typ
...      - 根据题目调整问题数量
7_sensitivity.typ
8_evaluation.typ
A_code.typ
```

中文统计建模各节文件：

```text
1_introduction.typ
2_method.typ
3_data.typ
4_analysis.typ
5_results.typ
6_conclusion.typ
A_code.typ
```

英文 MCM/APMCM 各节文件（`en/mcm`、`en/apmcm`、`zh/mcm`、`zh/apmcm`）：

```text
1_introduction.typ
2_assumptions.typ
3_model_design.typ
4_solution.typ
5_sensitivity.typ
6_strengths_weaknesses.typ
7_conclusions.typ
A_code.typ
```

**LaTeX 模板章节文件**（对应 `-latex` 后缀模板，结构与 Typst 版本一一对应）：

国赛 LaTeX 模板（`zh/cumcm-latex`，对应 `cumcm` Typst 版本）：

```text
1_restatement.tex
2_analysis.tex
3_assumptions.tex
4_symbols.tex
5_problem1.tex
6_problem2.tex
7_problem3.tex
8_sensitivity.tex
9_evaluation.tex
10_conclusion.tex
A_appendix.tex
A_code.tex
```

MCM/ICM LaTeX 模板（`en/mcm-latex`）：

```text
1_introduction.tex
2_assumptions.tex
3_model_design.tex
4_solution.tex
5_sensitivity.tex
6_strengths_weaknesses.tex
7_conclusions.tex
A_code.tex
```

其余 LaTeX 模板（`changsanjiao-latex`、`default-latex`、`huashubei-latex`、`mathorcup-latex`、`wuyibei-latex`、`huazhongbei-latex`、`huaweibei-latex`、`diangongbei-latex`、`dongsansheng-latex`、`shuweibei-latex`、`stats-latex`、`apmcm-latex`、`mcm-latex`、`en/apmcm-latex`、`en/default-latex`）的章节文件命名与上述结构类似，以 `main.tex` 中 `\input{}` 引用的文件名为准。

英文默认模板（`en/default`）：

```text
1_introduction.typ
2_assumptions.typ
3_notations.typ
4_model.typ
5_sensitivity.typ
6_evaluation.typ
7_conclusions.typ
A_code.typ
```

**正文写作应使用连贯的学术段落。避免在最终论文中出现工作流内部名称，如 `reports/`、`figures/` 或 `CLAUDE.md`。**

引言或问题重述部分应明确交代研究意义，并用真实可核验的参考文献概述相关研究或方法现状；不要为了凑结构虚构文献。结尾应按子问题汇总结论，并在赛题适用时给出由结果支撑的建议或启示。若比赛模板另有固定结构，以模板为准，并在验收记录中说明等价位置。

正文只保留理解模型所需的伪代码或短代码片段。完整程序和长代码块放入附录或支撑材料；不得用大段源码挤占正文。

### 步骤 5：参考文献

只使用真实存在的参考文献。文件名按引擎选择：Typst 用 `paper/references.typ`，LaTeX 用 `paper/references.tex`。

CUMCM 2026 中文论文必须先按真实使用情况写完“AI 工具使用声明”，再排参考文献。使用 AI 时，同时生成支撑材料中的 `AI工具使用详情.pdf`，内容覆盖工具名称/版本或型号、使用目的和环节、主要提示方式与过程、采纳/人工修改/核验情况。不能仅生成论文中的一句声明而遗漏详情文件。

**Typst 引擎**：

```typst
#set enum(numbering: "[1]")
#enum[
  作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  Author. "Title." Journal or Conference, year.
]
```

正文上标引用：`相关研究已用于物流网络优化#super("[1]")。`

**LaTeX 引擎**：

```latex
\begin{thebibliography}{99}
  \bibitem{ref1} 作者. 题名[J]. 期刊名, 年份, 卷(期): 页码.
  \bibitem{ref2} Author. "Title." Journal, year.
\end{thebibliography}
```

正文引用用 `\cite{ref1}` 或 `\cite{ref1,ref2}`。

### 步骤 6：最后撰写摘要或总结

在所有章节完成后撰写中文摘要或英文 Summary Sheet。必须包含每个子问题的方法和精确的数值结果。摘要不插入图、表、代码块或复杂推导公式。

CUMCM 中文论文还执行以下写作质量检查：论文标题应概括研究对象、核心方法或主要目标，不原样照抄赛题标题；关键词取 3--5 个能代表对象、模型或方法的术语，用中文或英文分号分隔，不把 Python、MATLAB、Excel 等软件名当作关键词。这些是写作质量建议，不替代当期官方格式规则；若官方通知另有要求，以官方通知为准。

## LaTeX 写作要点

以下要点供 **LaTeX 引擎**使用。Typst 引擎请调用 typst-author skill 获取语法帮助。

### 编译命令

使用步骤 3 的“图片路径与编译目录”约定。中文和英文均从入口文件所在目录执行两遍 xelatex，使用实际入口文件名。

### 文档结构

```latex
\documentclass[a4paper,12pt]{article}   % 英文
\documentclass[a4paper,12pt]{ctexart}   % 中文

\usepackage{...}   % 宏包加载
\usepackage{graphicx}   % 图片支持
\usepackage{booktabs}   % 三线表
\usepackage{amsmath,amssymb}   % 数学公式
\usepackage{hyperref}   % 交叉引用（需两遍编译）
```

### 图表插入

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth]{../figures/fig_q1.pdf}
  \caption{图注}
  \label{fig:q1}
\end{figure}

% 三线表
\begin{table}[htbp]
  \centering
  \caption{表注}
  \begin{tabular}{ccc}
    \toprule
    \textbf{列1} & \textbf{列2} & \textbf{列3} \\
    \midrule
    数据 & 数据 & 数据 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 交叉引用

图、表和需要引用的行间公式统一使用模板自动编号。标题或正文源文件中不得手写“图 1”“表 2”“式（3）”等编号；Typst 在对象后添加 `<fig:...>`、`<tab:...>`、`<eq:...>` 标签并用 `@标签` 引用，LaTeX 使用 `\label{}` 与 `\ref{}`/`\eqref{}`。无须引用的推导可使用明确的无编号公式环境。

```latex
如图~\ref{fig:q1}所示，...   % 图片引用
式~(\ref{eq:objective}) 给出...   % 公式引用
见第~\pageref{fig:q1} 页   % 页码引用
```

### 数学公式

```latex
行内公式：$f(x) = \sum_{i=1}^n \theta_i \phi_i(x)$

行间公式：
\begin{equation}
  \mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2
  \label{eq:objective}
\end{equation}
```

### 章节和强调

```latex
\section{问题重述}
\subsection{问题背景}
\textbf{问题一：} xxx   % 对应 Typst 的 #strong
```
