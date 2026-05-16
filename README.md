# Team Agent Workflow

A Claude Code plugin that deploys a 5-agent team workflow with enforcement hooks, decision memory, and research routing.

## Problem

- **Context explosion**: Long sessions degrade past 300-400k tokens
- **Cross-session knowledge loss**: `/clear` loses decision reasoning, rejected approaches, development biases
- **Subagent slacking**: Pure protocol-driven agents skip steps and cut corners
- **Self-knowledge overconfidence**: Models code from stale training data without verifying

## Solution

### 5-Agent Team

| Agent | Model | Role |
|-------|-------|------|
| **Coordinator** (Main) | Opus | Architecture decisions, task decomposition, dispatch |
| **Test Agent** | Sonnet → Opus | Testing with model escalation on failure |
| **Implementer** | Sonnet | Code execution in isolated worktree |
| **Explorer** | Sonnet | Read-only codebase research |
| **Decision Recorder** | Sonnet | Logs decisions to mem0 at mandatory nodes |
| **Reviewer** | Sonnet | Independent read-only audit (1:3-4 ratio) |

### 3 Hardcore Standards

1. **Do not over-trust self-knowledge** — research before coding when knowledge gap > 6 months
2. **Disagreements require evidence** — cite sources when pushing back on user decisions
3. **Research before proposing** — search 2-3 implementations before suggesting approaches

### 4 Enforcement Hooks

| Hook | Event | Action |
|------|-------|--------|
| Reviewer reminder | SubagentStop | Reminds Coordinator to audit implementer/test output |
| Decision reminder | PreToolUse (Write/Edit) | Reminds about unrecorded decision nodes |
| State reset | UserPromptSubmit | Resets nudge counters |
| End-of-session | Stop | Warns about decisions that will be lost |

### MCP Integration

- **mem0** — Cross-session decision memory via `add_memory` / `search_memories`
- **Context7** — Version-specific library docs via `resolve-library-id` / `query-docs`
- **Exa** — High-precision semantic search for tech research
- **Playwright** — Browser automation for E2E testing

### Integrated Principles

- [Karpathy Guidelines](https://github.com/multica-ai/andrej-karpathy-skills) — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution
- [PrismV3 Handoff System](https://github.com/) — File state machine, handoff format, behavioral red lines

## Install

```bash
claude plugin add <github-repo-url>
```

## Deploy to a Project

After installing the plugin, invoke the deployment skill in any project:

```
Use the workflow-deploy skill to set up this project
```

This copies rules to `.claude/rules/` and initializes state files.

## File Structure

```
.claude-plugin/plugin.json      Plugin metadata
agents/                         5 agent definitions (auto-loaded)
hooks/                          4 enforcement hooks (auto-loaded)
rules/                          8 rule files (deployed per project)
skills/workflow-deploy/         Deployment skill
```

## Sources

- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)
- [FlorianBruniaux/agent-teams guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide)
- [barkain/claude-code-workflow-orchestration](https://github.com/barkain/claude-code-workflow-orchestration)
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
- [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents)
- [Mem0 MCP](https://docs.mem0.ai/platform/features/mcp-integration)
- [Context7 MCP](https://github.com/upstash/context7)

## License

MIT
