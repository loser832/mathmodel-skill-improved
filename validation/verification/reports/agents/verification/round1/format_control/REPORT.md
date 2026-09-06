# V0 格式、文本与编译条件审查

- 角色：阶段总控 `/root/forward_verification`；本项是总控检查，不计作独立子 agent 审查。
- 范围：6verity Step 1–4、6–8；数学一致性和代码复现分别由 V1、V2 独立负责。
- 输入版本：本目录 `input_manifest.json` 中 8 个 SHA256；执行目录为本目录 `project`，保留原项目布局。
- 生产源文件只读；未修复任何产物。

## 实际检查

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| 文本门禁 | PASS | 真实运行 skill 的 writing_check.sh，exit 0，日志 writing_check.log；这只代表文本门禁。 |
| 单问章节结构 | PASS | paper/main.tex:4 仅引入 sections/1_solution；该文件存在、仅一个一级标题（:1），与 plan.md:5 的单问一致。 |
| 占位符、内部文件泄露 | PASS | 门禁及 rg 复核未命中；无正文列表、无图后说明问题。 |
| 图片/表格引用 | PASS | 无图表文件、无 includegraphics、caption、表格或交叉引用；按当前小型合成题范围无待核图表。 |
| 语言约定 | FAIL | plan.md:4 明确中文，paper/sections/1_solution.tex:1–4 的标题及正文均英文；要求与交付不一致。 |
| 正文长度 | WARN | 门禁报告 section 332 chars；对单问合成样例不另加虚构篇幅要求。 |
| 参考文献 | WARN | 无文献文件，也没有 cite/bibliography/thebibliography；无悬空引文。题目为自含基础线性规划，不将没有外部文献升级为来源造假或硬错误。 |
| 比赛模板要求 | WARN | 当前为 article + amsmath，未提供具体赛事/模板要求；不能确认封面/摘要页规范，也不能据此认定被删除了必需模板结构。 |
| 真实论文编译 | NOT_RUN | Get-Command xelatex 未返回可调用命令；以下 4 个常规路径检查均 false。未运行 xelatex 编译，也未初始化或安装环境。父协调者提示现有捆绑环境此前启动失败，此提示不是本轮实际编译证据。不能断言整机绝对无编译器。 |
| PDF 非空/页数/尺寸 | NOT_RUN | 原样例与本轮副本均无 PDF，本轮未取得编译产物。 |
| 逐页视觉检查 | NOT_RUN | 无可用本轮编译 PDF；未导出 PNG、未逐页目视。pdftoppm 已可定位，但不能替代缺少 PDF 的前置条件。 |

## 命令与运行条件

- 已启动：`E:\modex\Modex-MH-Agent\runtime\python\python.exe --version` → Python 3.11.9，exit 0。
- 已启动：`E:\modex\Modex-MH-Agent\runtime\git\bin\bash.exe --version` → GNU bash 5.2.37，exit 0。
- 门禁通过 Git Bash 进程内的 `python3` 函数路由到上述既有 Python，不创建全局 shim、不修改 PATH、不安装或初始化环境。
- 门禁完整脚本见 `gate_run.sh`；工作目录为本目录 `project`。日志 `writing_check.log` 最后一行为 `writing_check exit: 0`。
- 附加只读检查：`rg -n` 搜索入口、章节、图表、引文、占位符、内部路径；逐行读取 plan.md、主文件及正文章节以记录定位。

编译器路径探测（均 false）：

1. C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe
2. %USERPROFILE%\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe
3. C:\texlive\2026\bin\windows\xelatex.exe
4. C:\texlive\2025\bin\windows\xelatex.exe

已有 PDF 光栅器（仅定位，未调用导出）：

`%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe`

## 建议与边界

由 5writing 根据中文约定处理正文语言；取得可以启动且已经配置完成的 XeLaTeX 环境后，在新独立副本中双次编译，再进行基础 PDF 检查和逐页视觉检查。本轮只记录返工与恢复条件，不执行修复。数学结论及代码复现以对应独立报告为准。
