# Team Agent Workflow — 团队 Agent 工作流

[English](README.md)

一个 Claude Code marketplace 插件，部署 5-agent 团队工作流，含 4 个执行 hook、决策记忆（mem0）和调研路由（Context7 + Exa）。

## 解决的问题

| 痛点 | 根因 | 表现 |
|------|------|------|
| Context 爆炸 | 长会话超过 300-400k tokens 后智能退化 | HANDOFF-LOG 膨胀到 258KB，推理质量下降 |
| 跨 session 知识断层 | Handoff 传"做了什么"但不传"为什么不做那个" | /clear 后决策推理、排除原因、做事偏好全部丢失 |
| Subagent 偷懒 | 纯协议驱动依赖模型自觉 | 省略步骤、降低质量、重复造轮子 |
| 自我知识过度自信 | 模型训练截止与当前日期差距大 | 基于过时 API 写代码，不调研就行动 |

## 方案

### 5-Agent 团队

```
┌──────────────────────────────────────────┐
│           Main (Coordinator)             │
│          Model: Opus (session)           │
│   职责: 架构决策、任务分解、调度          │
│   决策节点强制调用 Decision Recorder     │
└─────┬──────┬──────┬──────┬──────┬───────┘
      │      │      │      │      │
  ┌───▼──┐┌──▼───┐┌──▼──┐┌──▼───┐┌──▼─────┐
  │Test  ││Imple ││Expl ││Deci  ││Reviewer│
  │Agent ││ment  ││orer ││sion  ││        │
  │      ││er    ││     ││Recor ││(只读)  │
  │Sonnet││Sonn  ││Sonn ││der   ││        │
  │→Opus ││et    ││et   ││Sonnet││Sonnet  │
  └──────┘└──────┘└─────┘└──────┘└────────┘
```

| Agent | Model | 职责 |
|-------|-------|------|
| **Coordinator** (Main) | Opus | 架构决策、任务分解、调度 |
| **Test Agent** | Sonnet -> Opus | 测试，连续失败 2 次自动升级到 Opus |
| **Implementer** | Sonnet | 在隔离 worktree 中执行编码 |
| **Explorer** | Sonnet | 只读代码探索（后台运行） |
| **Decision Recorder** | Sonnet | 在强制决策节点记录到 mem0 |
| **Reviewer** | Sonnet | 独立只读审计（比例 1:3-4） |

### 三条硬核标准

**标准 1: 不过度相信自我知识**
- 模型知识截止与当前日期差距 > 6 个月时，必须先调研再行动
- 调研路由：库 API -> Context7，架构模式 -> Exa，竞品 -> WebSearch
- 禁止：直接基于训练知识写代码不验证

**标准 2: 反驳开发者要有证据**
- 不同意用户技术决策时，必须给出具体论据 + 至少一个可验证的源引用
- 引用格式：`[来源标题](URL) — "相关原文摘要"`
- 找不到证据 -> 说明是推测，让用户决定
- 禁止："根据最佳实践" 不说是哪个实践、谁定义的

**标准 3: 先调研别人的工作流**
- 涉及工作流设计 / 工具选型 / 架构决策时，先搜索 2-3 个同类实现
- 提炼核心模式和 trade-off -> 对照当前约束做对比 -> 然后才提方案
- 禁止：直接基于训练知识提方案不调研

### 4 个执行 Hook（协议为主，Hook 兜底）

| Hook | 事件 | 作用 |
|------|------|------|
| Reviewer 审计提醒 | SubagentStop | Implementer/Test Agent 完成时提醒 Coordinator 调用 Reviewer |
| 决策记录提醒 | PreToolUse (Write/Edit) | 检测到未记录的决策节点时提醒 |
| 状态重置 | UserPromptSubmit | 每轮用户输入重置 nudge 计数器 |
| Session 结束提醒 | Stop | 警告有未记录的决策即将在 /clear 后丢失 |

所有 hook 为**提醒型**（stdout 注入），不是阻断型。理由：Main 是 Opus + max effort，提醒遵守率已经很高。

### MCP 集成

| MCP | 用途 |
|-----|------|
| **mem0** | Decision Recorder 的存储后端，跨 session/跨工具决策记忆 |
| **Context7** | 版本精确的库文档查询，防止 API hallucination |
| **Exa** | 高精度语义搜索（技术调研主力） |
| **Playwright** | 浏览器自动化 E2E 测试 |

### 调研路由表

```
1. 库/框架 API 精确查询    -> Context7 resolve-library-id -> query-docs
2. 技术趋势/最佳实践       -> Exa web_search_exa -> 回退: WebSearch
3. 竞品/替代方案           -> WebSearch -> WebFetch 精读
4. 具体页面内容提取         -> WebFetch (已知 URL)
5. 团队历史经验            -> mem0 search_memories
```

### 集成原则

- [Karpathy 四原则](https://github.com/multica-ai/andrej-karpathy-skills) — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution
- PrismV3 Handoff 系统 — 文件状态机 (`READY_FOR_IMPL -> READY_FOR_REVIEW -> READY_FOR_QA -> DONE`)，step->verify 格式，行为红线

### Handoff 格式（从 PrismV3 迁移并增强）

```markdown
# Handoff: {from} -> {to}

## 状态: READY_FOR_{NEXT}
## 任务: {一句话}
## 输入文件: {列表}
## 禁止触碰: {列表}

## 执行计划 (step->verify):
1. [步骤] -> verify: [检查方式]
2. [步骤] -> verify: [检查方式]

## 产出物:
- {文件路径}: {简要说明}

## 验证结果:
- Step 1: PASS/FAIL — {证据}

## 决策上下文:
- 已选方案: {摘要}
- 已排除方案: {摘要 + 原因}（详见 mem0 decision ID）
```

## 安装

```bash
# 第 1 步：添加 marketplace
/plugin marketplace add Jaydenlk/jayden-workflow

# 第 2 步：安装插件
/plugin install team-agent-workflow@jayden-workflow
```

## 部署到项目

安装后在任何项目中调用部署 skill：

```
/team-agent-workflow:workflow-deploy
```

自动完成：
1. 复制 8 个 rules 文件到 `.claude/rules/`
2. 初始化 `.claude/state/` 追踪文件
3. 检查 mem0 和 Context7 MCP 是否就绪
4. 输出验证报告

## 自动加载 vs 按项目部署

| 组件 | 作用域 | 加载方式 |
|------|--------|---------|
| 5 个 agents | 所有项目 | 插件自动加载 |
| 4 个 hooks | 所有项目 | 插件自动加载 |
| 8 个 rules | 按项目 | 通过 skill 部署 |
| State 文件 | 按项目 | 通过 skill 部署 |
| MCP (mem0, Context7) | 用户级 | 手动配置（skill 引导） |

## 文件结构

```
.claude-plugin/
  plugin.json                 插件元数据
  marketplace.json            Marketplace 目录
agents/                       5 个 agent 定义（自动加载）
  test-agent.md               测试 agent（Sonnet->Opus 升级）
  implementer.md              编码 agent（worktree 隔离）
  explorer.md                 探索 agent（只读，后台）
  decision-recorder.md        决策记录 agent（mem0 MCP）
  reviewer.md                 审计 agent（只读，找茬思想）
hooks/
  hooks.json                  Hook 事件注册
  subagent_stop.py            Hook 1: Reviewer 审计提醒
  pre_tool_use.py             Hook 2: 决策记录提醒
  user_prompt_submit.py       Hook 3: 状态重置
  session_stop.py             Hook 4: Session 结束提醒
rules/                        8 个规则文件（按项目部署）
  hardcore-standards.md       三条硬核标准
  karpathy-guidelines.md      Karpathy 四原则
  research-routing.md         调研路由表
  decision-nodes.md           决策节点枚举
  team-protocol.md            团队调度协议
  anti-slacking.md            反偷懒规则
  handoff-format.md           Handoff 文件格式
  goal-driven-execution.md    step->verify 模板
skills/workflow-deploy/       部署 skill
docs/superpowers/             设计 spec + 实现 plan
```

## 引用来源

- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) — Context rot 阈值，CLAUDE.md < 200 行
- [FlorianBruniaux/agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) — MAX_ITERATIONS，1:3-4 reviewer 比例
- [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration) — Hook 驱动执行，adaptive nudge
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — Goal-Driven Execution，Surgical Changes
- [Claude Code subagent 官方文档](https://code.claude.com/docs/en/sub-agents) — Agent 定义格式，model 选择，memory scope
- [Mem0 MCP](https://docs.mem0.ai/platform/features/mcp-integration) — 11 个工具，cloud MCP 配置
- [Context7 MCP](https://github.com/upstash/context7) — 版本精确的库文档

## License

MIT
