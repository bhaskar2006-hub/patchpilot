# Agent Skill Open Standard Specification for PatchPilot

## Overview
PatchPilot implements the [Agent Skill Open Standard](https://github.com/agent-skills), ensuring interoperability with modern agent runtimes (Antigravity, Claude Code, Cursor, OpenCode, Codex).

## Specification Structure
- `SKILL.md`: Main capability manifest with standard YAML frontmatter (`name`, `description`).
- `scripts/`: Direct execution scripts.
- `references/`: Supporting documentation, AST grammar schemas, and runtime guidelines.
- `tests/`: Automated unit & integration verification for the skill itself.

## Standard Invocations

Agents can discover and invoke PatchPilot directly via CLI or subprocess:

```json
{
  "name": "patchpilot",
  "command": "patchpilot heal --cmd \"pytest\" --commit"
}
```
