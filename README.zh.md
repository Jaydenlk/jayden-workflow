# Team Agent Workflow — 团队 Agent 工作流

一个 Claude Code 插件，部署 5-agent 团队工作流，含执行 hook、决策记忆和调研路由。

## 问题

- **Context 爆炸**：长会话超过 300-400k tokens 后智能退化
- **跨 session 知识断层**：`/clear` 后决策推理、排除原因、做事偏好全部丢失
- **Subagent 偷懒**：纯协议驱动的 agent 会省略步骤、降低质量
- **自我知识过度自信**：基于过时训练数据写代码，不调研就行动

## 方案

### 5-Agent 团队

| Agent | Model | 职责 |
|-------|-------|------|
| **Coordinator** (Main) | Opus | 架构决策、任务分解、调度 |
| **Test Agent** | Sonnet → Opus | 测试，失败时升级模型 |
| **Implementer** | Sonnet | 在隔离 worktree 中执行编码 |
| **Explorer** | Sonnet | 只读代码探索 |
| **Decision Recorder** | Sonnet | 在强制决策节点记录到 mem0 |
| **Reviewer** | Sonnet | 独立只读审计（1:3-4 比例） |

### 三条硬核标准

1. **不过度相信自我知识** — 知识差距 > 6 个月时必须先调研再写代码
2. **反驳要有证据** — 不同意用户决策时必须附源引用
3. **先调研别人的** — 提方案前搜索 2-3 个同类实现

### 4 个执行 Hook

| Hook | 事件 | 作用 |
|------|------|------|
| Reviewer 提醒 | SubagentStop | 提醒 Coordinator 审计 implementer/test 产出 |
| 决策提醒 | PreToolUse (Write/Edit) | 提醒未记录的决策节点 |
| 状态重置 | UserPromptSubmit | 重置 nudge 计数器 |
| Session 结束 | Stop | 警告即将丢失的决策 |

### MCP 集成

- **mem0** — 跨 session 决策记忆
- **Context7** — 版本精确的库文档
- **Exa** — 高精度语义搜索
- **Playwright** — 浏览器自动化 E2E 测试

### 集成原则

- [Karpathy Guidelines](https://github.com/multica-ai/andrej-karpathy-skills) — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution
- PrismV3 Handoff System — 文件状态机、handoff 格式、行为红线

## 安装

```bash
claude plugin add <github-repo-url>
```

## 部署到项目

安装插件后，在任何项目中调用部署 skill：

```
使用 workflow-deploy skill 部署到当前项目
```

这会复制 rules 到 `.claude/rules/` 并初始化 state 文件。

## 文件结构

```
.claude-plugin/plugin.json      插件元数据
agents/                         5 个 agent 定义（自动加载）
hooks/                          4 个执行 hook（自动加载）
rules/                          8 个规则文件（按项目部署）
skills/workflow-deploy/         部署 skill
```

## 引用来源

- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)
- [FlorianBruniaux/agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide)
- [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration)
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
- [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents)
- [Mem0 MCP](https://docs.mem0.ai/platform/features/mcp-integration)
- [Context7 MCP](https://github.com/upstash/context7)

## License

MIT
