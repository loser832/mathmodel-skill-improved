# Mathmodel Skill Improved

这是一个面向数学建模竞赛的 Agent skills 工作流改进版，重点增强了偏好继承、图片路径约定、验收返工、按需多 agent 协作，以及有界的结构化交叉质询。

本仓库只发布工作流、修改记录和合成验证材料，不包含实际赛题、附件或个人竞赛成果。

## 主要内容

- `skills/`：可安装的工作流快照，包括入口、建模、编程与数据图表、DrawIO、论文写作、最终验收和共享规范。
- `skills/1start-mathmodel/references/multi-agent.md`：多 agent 协作、独立首稿、证据仲裁和结构化交叉质询协议。
- `MODIFICATION_RECORD.md`：本轮及前序优化的完整说明。
- `validation/`：静态检查和隔离的合成建模、验收场景；这些材料不是实际比赛成果。
- `changes-multi-agent.diff`：关键协作改动的逐行差异。

本机备份、历史快照、安装回执、赛题目录及其生成产物均通过 `.gitignore` 留在本地，不纳入公开仓库。

## 安装

将 `skills/` 下的目录复制到 Codex/Agent 的个人 skills 目录。Windows PowerShell 示例：

```powershell
$targetSkills = Join-Path $env:USERPROFILE ".agents\skills"
New-Item -ItemType Directory -Force $targetSkills | Out-Null
Copy-Item -Recurse -Force ".\skills\*" $targetSkills
```

共享的 `typst-author` 等外部 skills 仍需单独安装；本仓库不是全部工具依赖的离线发行包。

安装后，在数学建模项目中调用 `1start-mathmodel`，由入口 skill 按阶段组织分析、建模、代码与图表、流程图、论文写作和最终验收。

## 项目来源与许可

本项目基于 [jihe520/MathModelAgent](https://github.com/jihe520/MathModelAgent) 的 skills 进行个人、非商业修改，并保留可追溯的差异与验证记录。使用和再分发须遵守上游的非商业与开放分发限制，详见 [LICENSE.md](LICENSE.md)。模板中的赛事标识、标题页素材及其他第三方资产，其权利仍归各自权利人所有。
