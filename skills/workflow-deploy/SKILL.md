---
name: workflow-deploy
description: Deploy the Team Agent workflow to the current project. Sets up project-level rules, state directory, and verifies MCP config. Agents and hooks are auto-loaded by the plugin. Run this when starting a new project that should use the team agent workflow.
---

# Deploy Team Agent Workflow

You have been invoked to deploy the Team Agent workflow to the current project.

## What the Plugin Already Provides (auto-loaded)

The following are active the moment the plugin is installed — no action needed:
- **5 agents**: test-agent, implementer, explorer, decision-recorder, reviewer
- **4 hooks**: SubagentStop → reviewer reminder, PreToolUse → decision reminder, UserPromptSubmit → state reset, Stop → end-of-session reminder

## What You Need to Deploy (project-level)

### Step 1: Create project rules directory

Copy all `.md` files from this plugin's `rules/` directory to the current project's `.claude/rules/` directory. These rules auto-load when Claude Code starts in this project.

The plugin's rules directory is at the path where this skill was loaded from (go up two levels from this SKILL.md to find `rules/`). Read each file and write it to `.claude/rules/` in the current project.

### Step 2: Create state directory

Create `.claude/state/` in the project root with two initial files:

`decision-tracker.json`:
```json
{"pending_decisions": [], "nudge_count": 0}
```

`pending-reviews.json`:
```json
{"pending": []}
```

### Step 3: Verify MCP servers

Check if mem0 and Context7 MCP servers are available. If not, inform the user:

**mem0** (for Decision Recorder): Run `npx mcp-add --name mem0-mcp --type http --url "https://mcp.mem0.ai/mcp" --clients "claude code"`

**Context7** (for research routing): Run `npx ctx7 setup --claude`

### Step 4: Verify deployment

1. Confirm `.claude/rules/` has 8 `.md` files
2. Confirm `.claude/state/` has 2 `.json` files
3. Suggest user run `/agents` to verify 5 custom agents appear
4. Suggest user run `/hooks` to verify 4 hooks are registered

### Step 5: Report

Tell the user what was deployed and any remaining manual steps (MCP setup if needed).
