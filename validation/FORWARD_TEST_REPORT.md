# 多 agent 协作行为验证

日期：2026-09-04。使用 E:/mathmodel/skills 中本轮文件，在两个隔离的合成项目中调用真实 agent。两轮演练均已完成，关键行为符合预期；测试快照与实际安装内容一致。

## 建模场景：通过

输入：两中心、三客户的容量约束配送题，共两个顶层问题；基准客户需求均为 6，中心容量均为 10，后续需求增长 20%；题面未说明客户能否拆单。

原计划已选择 Typst、中文、auto，允许最多两名子 agent。阶段总控 `/root/forward_modeling` 实际启动两个独立专家：

- `/root/forward_modeling/model_proposal`：独立模型方案。
- `/root/forward_modeling/assumption_review`：题意、假设与反例检查。

两个专家均已完成，只读同版本输入，分别写自身目录，未递归招募。总控实际读取报告后整合；没有重复询问偏好，也没有越界执行生产代码或写作。

关键观察：两种解释得到不同结论。允许拆单时给出可行解 A=(6,2,0)、B=(0,4,6)，费用下界 218 可达；单客户单中心时，至少一个中心负载 12>10，基准不可行。增长后总需求 21.6>20，原资源约束下不可行。总报告显式保留歧义及证据，仍只有两个顶层问题；未因多个专家结论一致而把业务假设视为题面已确定事实。

来源五项哈希结束复核未变；正式数值求解、论文编译和作图明确未执行。报告中的数值是建模阶段解析验算依据。

证据：[总报告](modeling/reports/ANALYSIS_MODELING_REPORT.md)、[协作记录](modeling/reports/COLLABORATION_LOG.md)、[来源清单](modeling/reports/SOURCE_MANIFEST.json)、[模型专家](modeling/reports/agents/modeling/round1/model_proposal/REPORT.md)、[反例专家](modeling/reports/agents/modeling/round1/assumption_review/REPORT.md)。

## 验收场景：行为符合预期，样例结论 FAIL

输入为最小化 3x+2y，满足 x+y≥10 且 x,y≥0 的单问合成题。模型和结果记录给出 x=0、y=10、目标值 20，论文中目标值写为 23。计划明确中文、LaTeX、multi、最多两名子 agent；本次仅验收，不修复。

阶段总控 `/root/forward_verification` 实际按可用名额分批启动两名独立子 agent：`math_numeric` 检查数学与论文数值，`code_reproduction` 在独立副本复现代码。总控负责文本/格式检查与唯一验收报告；没有把总控检查算成第三名独立专家。

观察结果：

- 数学审查证明全局下界为 20，识别论文 23 的错误，将返工指向 `5writing`，没有要求更改正确结果。
- 代码复现实际运行一次，退出码 0，输出 x=0、y=10、objective=20、feasible=true，与记录完全一致；只证明这个固定合成案例的复现，不称通用求解器已经验证。
- 文本门禁实际退出 0，但总控没有据此忽略语义数值错误；同时发现英文正文与中文计划冲突。
- 真实论文编译、PDF 基础检查和逐页视觉检查记为 `NOT_RUN`。未将缺失证据补成通过，也未以 `BLOCKED` 掩盖已知硬错误；样例最终为 `FAIL`、不具备提交条件。
- 所有审查输出均位于独立目录；八项原始输入的结束哈希一致。父总控再次计算八项哈希亦全部匹配，确认只审查未修复。

证据：[验收总报告](verification/reports/VERIFY_REPORT.md)、[数学审查](verification/reports/agents/verification/round1/math_numeric/REPORT.md)、[代码复现](verification/reports/agents/verification/round1/code_reproduction/REPORT.md)、[原始运行记录](verification/reports/agents/verification/round1/code_reproduction/run.json)、[文本门禁日志](verification/reports/agents/verification/round1/format_control/writing_check.log)、[源文件校验](verification/reports/agents/verification/round1/format_control/source_integrity.json)。

两轮结果和父总控结束校验汇总见 [behavior-results.json](behavior-results.json)。

## 验证范围

这两次演练检查真实委派、角色分工、证据整合、源文件保护、既有偏好和状态规则。它们不是单 agent 与多 agent 的质量/耗时/费用对照试验，不能据此承诺多 agent 必然更优。

静态检查另见 [static-results.json](static-results.json)。未在本轮实际演练所有失败、超时和工具不可用的降级分支；这些边界已在协作协议中明文规定。本次也不以合成演练代替真实竞赛论文的编译和逐页视觉验收。
