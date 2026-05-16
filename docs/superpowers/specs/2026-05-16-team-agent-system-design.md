# Team Agent System Design — workflow0516

**Version**: 1.0
**Date**: 2026-05-16
**Status**: Approved
**Author**: Jayden park + Claude Opus 4.6

---

## 1. Problem Statement

PrismV3 项目暴露了以下工作流痛点，本设计旨在系统性解决：

| 痛点 | 根因 | PrismV3 现象 |
|------|------|-------------|
| Context 爆炸 | 长会话超过 300-400k tokens 智能退化 | HANDOFF-LOG.md 膨胀至 258KB/3374 行 |
| 跨 session 知识断层 | Handoff 传递"做了什么"但不传递"为什么不做那个" | /clear 后决策推理、排除原因、做事偏好全部丢失 |
| Subagent 偷懒 | 纯协议驱动依赖模型自觉 | Agent 省略步骤、降低质量、重复造轮子 |
| 自我知识过度自信 | 模型训练截止与当前日期差距大 | 基于过时 API 写代码，不调研就行动 |

**Sources**:
- Context rot thresholds: [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) — "300-400k tokens: intelligence degradation"
- Anti-slacking patterns: [agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md) — "MAX_ITERATIONS guardrail"
- Goal-Driven Execution: [Karpathy guidelines](https://github.com/multica-ai/andrej-karpathy-skills) — "Define success criteria. Loop until verified."

---

## 2. Design Principles

### 2.1 三条硬核标准（Universal，跨项目生效）

**标准 1: 不过度相信自我知识**
- 当模型知识截止日期与当前日期差距 > 6 个月时，涉及框架 API / 架构模式 / 生态变化的任务必须先调研
- 调研路由：库 API → Context7，技术趋势 → Exa，竞品 → WebSearch，具体页面 → WebFetch
- 不允许：直接基于训练知识写代码而不验证

**标准 2: 反驳开发者要有证据**
- 不同意用户技术决策时，必须给出具体技术论据 + 至少一个可验证的源引用（URL 或文档路径）
- 引用格式：`[来源标题](URL) — "相关原文摘要"`
- 找不到支持证据 → 说明是推测，让用户决定
- 不允许："根据最佳实践" 不说是哪个实践、谁定义的

**标准 3: 先调研别人的工作流**
- 涉及工作流设计 / 工具选型 / 架构决策时，先用 Exa/WebSearch 搜索 2-3 个同类实现
- 提炼核心模式和 trade-off → 对照当前约束做对比 → 然后才提方案
- 不允许：直接基于训练知识提方案而不调研

### 2.2 Karpathy 四原则（集成）

1. **Think Before Coding** — 不假设、不隐藏困惑、呈现多个解读
2. **Simplicity First** — 最少代码解决问题，不做投机性功能
3. **Surgical Changes** — 只改必须改的，每行改动追溯到需求
4. **Goal-Driven Execution** — 任务转化为可验证目标，step→verify 格式

Source: [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)

### 2.3 开发规则与验收标准

**按项目单独定义**，不写入 workflow 模板。每个项目在自己的 CLAUDE.md 中定义。

---

## 3. Agent Team Architecture

### 3.1 团队阵容

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

### 3.2 Agent 定义规格

#### Test Agent (`test-agent.md`)
- **Model**: Sonnet (default)，升级条件触发 Opus
- **Tools**: 全部
- **Memory**: project scope
- **MCP**: playwright
- **职责**: 单元测试、集成测试、E2E 测试
- **升级触发条件**:
  - Sonnet 测试连续失败 2 次
  - 涉及安全 / 支付 / 数据一致性等关键路径
  - 跨 2+ 模块的协调性测试
  - 测试没有定义明确 success criteria
  - 用户手动指定 `--model opus`

#### Implementer (`implementer.md`)
- **Model**: Sonnet
- **Tools**: 全部
- **Memory**: project scope
- **Isolation**: worktree
- **职责**: 按 handoff 文件执行编码任务
- **Handoff 格式必须包含 step→verify**:
  ```
  1. [步骤] → verify: [检查方式]
  2. [步骤] → verify: [检查方式]
  ```

#### Explorer (`explorer.md`)
- **Model**: Sonnet
- **Tools**: Read, Grep, Glob, Bash (readonly)
- **Memory**: none
- **Background**: true
- **职责**: 代码探索、结构调研、依赖分析

#### Decision Recorder (`decision-recorder.md`)
- **Model**: Sonnet
- **Tools**: Read, Grep, mem0 MCP tools
- **Memory**: project scope
- **职责**: 在决策节点强制记录决策推理过程
- **无 Write/Edit 权限** — 只能往 mem0 存，不能改代码

#### Reviewer (`reviewer.md`)
- **Model**: Sonnet
- **Tools**: Read, Grep, Glob
- **Memory**: project scope
- **职责**: 独立审计 subagent 产出
- **无任何写权限** — 纯审计
- **审计准则**:
  - [ ] 每一行改动是否能追溯到原始需求（Karpathy Surgical Changes）
  - [ ] 是否有 drive-by refactoring
  - [ ] 是否有 speculative features
  - [ ] 每步是否有对应的验证结果（Goal-Driven Execution）
  - [ ] handoff 文件的交付物清单是否全部完成
  - [ ] 代码质量是否符合项目标准
- **比例**: 1 Reviewer : 3-4 builders (ref: [agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md))

---

## 4. Decision Recorder System

### 4.1 Decision Schema (存入 mem0)

```json
{
  "decision_type": "选型|否决|架构变更|bug修复策略|依赖选择|方案确认|推翻旧决策",
  "context": "为什么在这个节点需要做决策",
  "chosen": "最终选择了什么",
  "rejected": [
    {
      "option": "被否决的方案",
      "reason": "否决原因",
      "evidence": "支持否决的证据/链接"
    }
  ],
  "tradeoffs": "选择带来的代价是什么",
  "related_decisions": ["之前的相关决策 ID"],
  "project": "项目名",
  "timestamp": "ISO 8601"
}
```

### 4.2 决策节点枚举

Main agent 在以下节点**必须**调用 Decision Recorder，不调就是违规：

| 节点 | 触发条件 | 必须记录 |
|------|---------|---------|
| brainstorming 选方案后 | brainstorming skill 完成 | chosen + rejected + tradeoffs |
| 否决用户提议时 | Main 不同意用户方案 | rejected + evidence (硬核标准 2) |
| bug 修复策略选择 | debugging skill 后确定修复路线 | chosen + rejected + context |
| 依赖/工具选型 | 选择某个库/工具而非另一个 | chosen + rejected + evidence |
| 架构变更 | 修改组件边界/数据流/接口 | full schema |
| 发现重复造轮子 | 已有方案但之前不知道 | context + related_decisions |
| 推翻之前的决策 | 改变之前确认过的方案 | full schema + related_decisions |

### 4.3 mem0 作为存储后端

- Decision Recorder 通过 mem0 MCP 的 `add_memory` 存入
- 跨 session 查询通过 `search_memories` 检索
- 记录格式由 Recorder 的 system prompt 硬性约束
- mem0 是"有纪律的存储后端"，不是"希望 agent 自觉的系统"

---

## 5. MCP Integration Layer

### 5.1 新增 MCP

| MCP | URL | 用途 |
|-----|-----|------|
| mem0 | `https://mcp.mem0.ai/mcp` | Decision Recorder 存储后端，跨 session/跨工具记忆 |
| Context7 | `https://mcp.context7.com/mcp` | 版本精确的库文档查询，防止 API hallucination |

### 5.2 保留 MCP

| MCP | 用途 |
|-----|------|
| Exa | 高质量语义搜索 + 网页抓取（技术调研主力） |
| Playwright | 浏览器自动化（E2E 测试 + 手动验证） |
| Gmail / Google Calendar / Google Drive | 办公集成 |
| Figma | 设计稿获取 |

### 5.3 调研路由表

```
1. 库/框架 API 精确查询
   → Context7 resolve-library-id → query-docs
   → 回退: WebFetch 官方文档 URL

2. 技术趋势/最佳实践/架构模式
   → Exa web_search_exa
   → 回退: WebSearch

3. 竞品/替代方案/社区经验
   → WebSearch → 筛选 → WebFetch 精读
   → 或 Exa web_search_exa + web_fetch_exa

4. 具体页面内容提取
   → WebFetch (已知 URL)
   → Exa web_fetch_exa (需要高质量提取)

5. 团队历史经验
   → mem0 search_memories
   → clouddreamai-knowledge project-debug / project-design
```

---

## 6. Hook Enforcement Layer

### 6.1 设计原则

- 协议为主，hook 兜底
- 4 个精选 hook（不是 14 个）
- 全部为**提醒型**（stdout 注入），不是阻断型
- 理由：Main 是 Opus + max effort，提醒遵守率高；阻断通过 exit code 会导致工具调用失败

### 6.2 Hook 定义

#### Hook 1: `SubagentStop` — Reviewer 审计提醒

```python
# .claude/hooks/subagent-stop.py
# 触发: 任何 subagent 完成时
# 逻辑: 检查 agent_type，如果是 implementer 或 test-agent，提醒 Reviewer 审计
```

当 implementer 或 test-agent 完成时，输出：
```
[HOOK] Subagent {agent_type} 已完成。根据团队协议，此产出必须经过 Reviewer 审计才能合入。
请调用 Reviewer Agent 进行独立审计。
```

#### Hook 2: `PreToolUse` — 决策记录提醒

```python
# .claude/hooks/pre-tool-use.py
# 触发: Main agent 调用 Write/Edit 时
# 逻辑: 检查 .claude/state/decision-tracker.json 是否有未记录的决策节点
```

当检测到未记录的决策时，输出：
```
[HOOK] 检测到本 session 有未记录的决策节点。
请先调用 Decision Recorder 记录决策推理过程，再继续编码。
```

#### Hook 3: `UserPromptSubmit` — 状态重置

```python
# .claude/hooks/user-prompt-submit.py
# 触发: 用户提交新 prompt 时
# 逻辑: 重置 nudge 计数器和决策追踪状态
```

#### Hook 4: `Stop` — Session 结束提醒

```python
# .claude/hooks/stop.py
# 触发: session 结束或 /clear 前
# 逻辑: 检查是否有未持久化的决策记录
```

当有未记录的决策时，输出：
```
[HOOK] 本 session 有未记录的决策。建议在结束前调用 Decision Recorder。
未记录的决策在 /clear 后将永久丢失。
```

---

## 7. Handoff System (从 PrismV3 迁移并增强)

### 7.1 文件状态机

```
READY_FOR_IMPL → READY_FOR_REVIEW → READY_FOR_QA → DONE
```

### 7.2 Handoff 文件格式 (增强版)

```markdown
# Handoff: {from} → {to}

## 状态: READY_FOR_{NEXT}
## 任务: {一句话}
## 输入文件: {列表}
## 禁止触碰: {列表}

## 执行计划 (step→verify):
1. [步骤] → verify: [检查方式]
2. [步骤] → verify: [检查方式]
3. [步骤] → verify: [检查方式]

## 已完成:
- {完成项 1}
- {完成项 2}

## 产出物:
- {文件路径}: {简要说明}

## 验证结果:
- Step 1: PASS/FAIL — {证据}
- Step 2: PASS/FAIL — {证据}

## 遗留问题:
- {如有}

## 决策上下文:
- 已选方案: {摘要}
- 已排除方案: {摘要 + 原因}（详见 mem0 decision ID）
```

### 7.3 从 PrismV3 迁移的规则

- 子 agent 启动时只读自己的 handoff 文件
- 子 agent 完成后必须更新自己的 handoff 文件
- 主 agent 在两个子 agent 之间做桥接
- 文件读取纪律：Grep/Glob 先确认目标，不允许"先读再看有没有用"
- 行为红线：不做任务外的事、不修改决策文件、不读其他 agent 的 handoff、不嵌套 subagent

---

## 8. File Structure

```
workflow0516/
├── CLAUDE.md                                    # < 200 行，路由到 rules/
├── .claude/
│   ├── settings.json                            # MCP 配置 + 权限
│   ├── agents/
│   │   ├── test-agent.md
│   │   ├── implementer.md
│   │   ├── explorer.md
│   │   ├── decision-recorder.md
│   │   └── reviewer.md
│   ├── rules/
│   │   ├── team-protocol.md                     # 团队调度协议
│   │   ├── research-routing.md                  # 调研路由表
│   │   ├── decision-nodes.md                    # 决策节点枚举
│   │   ├── hardcore-standards.md                # 三条硬核标准
│   │   ├── anti-slacking.md                     # 反偷懒规则
│   │   ├── handoff-format.md                    # Handoff 格式 (PrismV3 迁移+增强)
│   │   ├── karpathy-guidelines.md               # Karpathy 四原则
│   │   └── goal-driven-execution.md             # step→verify 模板
│   ├── hooks/
│   │   ├── subagent-stop.py                     # Hook 1
│   │   ├── pre-tool-use.py                      # Hook 2
│   │   ├── user-prompt-submit.py                # Hook 3
│   │   └── stop.py                              # Hook 4
│   └── state/
│       ├── decision-tracker.json                # 决策节点追踪
│       └── pending-reviews.json                 # 待审计列表
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-16-team-agent-system-design.md
```

---

## 9. Integration with Existing Ecosystem

### 9.1 与 superpowers skills 的关系

| Skill | 与 Agent 系统的交互 |
|-------|-------------------|
| brainstorming | 完成后触发 Decision Recorder |
| writing-plans | 生成 Implementer 的 handoff |
| test-driven-development | 由 Test Agent 执行 |
| systematic-debugging | 完成后触发 Decision Recorder |
| verification-before-completion | Reviewer 的审计依据 |
| requesting-code-review | 可委派给 Reviewer Agent |
| dispatching-parallel-agents | 用于并行启动多个 Implementer |
| using-git-worktrees | Implementer 的 isolation 机制 |

### 9.2 与 clouddreamai-knowledge 的关系

- `project-debug` — 提修复方案前查团队历史，Decision Recorder 也记录
- `project-design` — 设计前查最佳实践，补充 Exa/Context7 调研
- `project-verify` — 提交前查团队规范，Reviewer 也检查
- `save-experience` — 可复用经验保存，与 mem0 互补（团队级 vs 跨工具级）

### 9.3 与 auto memory 的关系

- auto memory 继续做**结构化项目记忆**（feedback/user/project/reference）
- mem0 做**决策推理记忆**（Decision Recorder 产出）
- 两层分工，不冲突

---

## 10. Context Management Strategy

### 10.1 防止 context 爆炸

- CLAUDE.md < 200 行（详细规则在 `.claude/rules/` 自动加载）
- Agent 隔离各自 context（subagent 只返回摘要，不返回探索过程）
- Decision Recorder 把决策推理存入 mem0（不留在 context 里）
- Handoff 文件是 "context 的持久化代理"，不是 "在 context 里堆历史"
- 40% context 使用率为警戒线，60% 考虑 /compact

### 10.2 跨 session 连续性

```
/clear 后重建 context 的路径:

1. CLAUDE.md + .claude/rules/ → 自动加载（团队规则、调度协议）
2. .claude/agents/ → 自动加载（agent 定义）
3. mem0 search_memories → 查询相关决策历史
4. auto memory → 查询 feedback/user/project/reference
5. Handoff 文件 → 查询上一个 session 的交付物状态
6. clouddreamai-knowledge → 查询团队级知识
```

这 6 层保证 /clear 后不会失忆。

---

## 11. Deployment Strategy

### 11.1 交付形态：Claude Code Skill + GitHub Plugin

整个 workflow 打包为一个 Claude Code skill/plugin：
- AI 读完 skill 内容后自动执行部署
- 用户只需 `claude plugin install` 或手动加载 skill
- GitHub repo 作为分发渠道，带 README

### 11.2 Skill 结构

```
workflow0516-skill/
├── .claude-plugin/
│   └── plugin.json                  # Plugin 元数据
├── skills/
│   └── workflow-deploy/
│       ├── SKILL.md                 # 部署指令（AI 读完自动执行）
│       └── templates/
│           ├── agents/              # 5 个 agent .md 模板
│           ├── rules/               # 8 个 rules .md 模板
│           ├── hooks/               # 4 个 hook .py 模板
│           └── configs/             # settings.json / .claude.json 片段
├── README.md                        # 项目说明 + 使用指南
├── README.zh.md                     # 中文说明
└── LICENSE
```

### 11.3 部署流程（Skill 自动执行）

```
1. 检查当前环境（Windows/Mac/Linux）
2. 部署 user-level agents → ~/.claude/agents/
3. 合并 hooks 到 ~/.claude/settings.json
4. 合并 MCP 到 ~/.claude.json (mem0 + context7)
5. 写入 ~/.claude/CLAUDE.md（通用规则，不覆盖已有内容）
6. [可选] 部署 project-level 模板到当前项目
7. 验证部署结果（/agents 检查 + /hooks 检查）
```

---

## 12. Sources

- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) — Context rot thresholds, CLAUDE.md < 200 lines
- [FlorianBruniaux/agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md) — MAX_ITERATIONS, kill & reassign, 1:3-4 reviewer ratio
- [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration) — Hook-based enforcement, adaptive nudge, wave parallelization
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) — Goal-Driven Execution, Surgical Changes, Simplicity First
- [Claude Code official docs: subagents](https://code.claude.com/docs/en/sub-agents) — Agent definition format, model selection, memory scope
- [Mem0 MCP Integration](https://docs.mem0.ai/platform/features/mcp-integration) — 11 tools, cloud MCP setup
- [Mem0 OpenMemory](https://mem0.ai/blog/introducing-openmemory-mcp) — Local-first memory, cross-tool persistence
- [Context7 MCP](https://github.com/upstash/context7) — Version-specific library docs, resolve-library-id + query-docs
- [Developers Digest: Agent Teams vs Subagents](https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026) — When to use each pattern, production workflow
- PrismV3 `.claude/rules/subagent-constraints.md` — File state machine, handoff format, behavioral red lines
- PrismV3 `workflow-snapshot-2026-05-02.md` — User workflow philosophy, skills chain, acceptance standards
