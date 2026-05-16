# Team Agent Workflow

[中文文档](README.zh.md)

A Claude Code plugin that deploys a 5-agent team workflow with enforcement hooks, decision memory, and research routing.

## Problem

| Pain Point | Root Cause | Symptom |
|-----------|-----------|---------|
| Context explosion | Sessions degrade past 300-400k tokens | HANDOFF-LOG grows to 258KB, intelligence drops |
| Cross-session knowledge loss | Handoff carries "what was done" but not "why not that" | Decision reasoning, rejected approaches lost after /clear |
| Subagent slacking | Protocol-driven agents self-police poorly | Steps skipped, quality drops, wheels reinvented |
| Self-knowledge overconfidence | Model training cutoff vs current date gap | Code based on stale APIs without verification |

## Solution

### 5-Agent Team

| Agent | Model | Role |
|-------|-------|------|
| **Coordinator** (Main) | Opus | Architecture decisions, task decomposition, dispatch |
| **Test Agent** | Sonnet -> Opus | Testing with model escalation on 2x failure |
| **Implementer** | Sonnet | Code execution in isolated worktree |
| **Explorer** | Sonnet | Read-only codebase research (background) |
| **Decision Recorder** | Sonnet | Logs decisions to mem0 at mandatory nodes |
| **Reviewer** | Sonnet | Independent read-only audit (1:3-4 ratio) |

### 3 Hardcore Standards

1. **Do not over-trust self-knowledge** -- research via Context7/Exa/WebSearch before coding when knowledge gap > 6 months
2. **Disagreements require evidence** -- cite verifiable sources (`[Title](URL) -- "quote"`) when pushing back
3. **Research before proposing** -- search 2-3 existing implementations before suggesting approaches

### 4 Enforcement Hooks

| Hook | Event | Action |
|------|-------|--------|
| Reviewer reminder | SubagentStop | Reminds Coordinator to audit implementer/test output |
| Decision reminder | PreToolUse (Write/Edit) | Warns about unrecorded decision nodes |
| State reset | UserPromptSubmit | Resets nudge counters per turn |
| End-of-session | Stop | Warns about decisions that will be lost after /clear |

### MCP Integration

| MCP | Purpose |
|-----|---------|
| **mem0** | Cross-session decision memory (`add_memory` / `search_memories`) |
| **Context7** | Version-specific library docs (`resolve-library-id` / `query-docs`) |
| **Exa** | High-precision semantic search for tech research |
| **Playwright** | Browser automation for E2E testing |

### Integrated Principles

- [Karpathy Guidelines](https://github.com/multica-ai/andrej-karpathy-skills) -- Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution
- PrismV3 Handoff System -- File state machine (`READY_FOR_IMPL -> READY_FOR_REVIEW -> READY_FOR_QA -> DONE`), step->verify format, behavioral red lines

## Install

```bash
# Step 1: Add marketplace
/plugin marketplace add Jaydenlk/jayden-workflow

# Step 2: Install plugin
/plugin install team-agent-workflow@jayden-workflow
```

## Deploy to a Project

After installing, invoke the deployment skill in any project to set up project-level rules and state:

```
/team-agent-workflow:workflow-deploy
```

This copies 8 rules files to `.claude/rules/` and initializes state tracking in `.claude/state/`.

## What Gets Auto-Loaded vs Deployed

| Component | Scope | Mechanism |
|-----------|-------|-----------|
| 5 agents | All projects | Auto-loaded by plugin |
| 4 hooks | All projects | Auto-loaded by plugin |
| 8 rules | Per project | Deployed via skill |
| State files | Per project | Deployed via skill |
| MCP (mem0, Context7) | User-level | Manual setup (skill guides you) |

## File Structure

```
.claude-plugin/
  plugin.json               Plugin metadata
  marketplace.json          Marketplace catalog
agents/                     5 agent definitions (auto-loaded)
hooks/
  hooks.json                Hook event registration
  *.py                      4 enforcement hook scripts
rules/                      8 rule files (deployed per project)
skills/workflow-deploy/     Deployment orchestrator skill
docs/superpowers/           Design spec + implementation plan
```

## Sources

- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) -- Context rot thresholds, CLAUDE.md < 200 lines
- [FlorianBruniaux/agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) -- MAX_ITERATIONS, 1:3-4 reviewer ratio
- [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration) -- Hook-based enforcement, adaptive nudge
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) -- Goal-Driven Execution, Surgical Changes
- [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents) -- Agent definition format, model selection, memory scope
- [Mem0 MCP](https://docs.mem0.ai/platform/features/mcp-integration) -- 11 tools, cloud MCP setup
- [Context7 MCP](https://github.com/upstash/context7) -- Version-specific library docs

## License

MIT
