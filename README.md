# OpenCode Agents Collection

This repository contains reusable OpenCode specialist-agent templates organized into curated team packs and standalone reference agents.

## Team Packs

- `a-team/` - lean, balanced product-delivery workflow for planning, discovery, design, implementation, validation, and documentation
- `a-team-plus/` - expanded shipping workflow that adds deployment, performance, security, accessibility, AI, and rapid prototyping coverage

## Reference Agents

- `reference-agents/` - standalone source/reference agent files kept outside the curated team packs
- `reference-agents/` files come from varied external sources; if you copy one into a curated pack or live setup, review and normalize it first for naming, permissions, prompt quality, and workflow consistency

## Which One To Use

Choose `a-team` when:

- you want a clean default team for most feature work
- deployment and infrastructure are occasional needs, not default workflow steps
- you prefer a smaller specialist set with lower coordination overhead

Choose `a-team-plus` when:

- the work includes deployment, CI/CD, or environment automation
- performance, security, or accessibility need to be first-class review lanes
- the feature includes AI integration or you want a dedicated prototype/MVP specialist
- you want a more comprehensive release workflow out of the box

## Structure

Each team pack uses the same layout:

```text
<team-name>/
  agents/
    *.md
  README.md
```

- `agents/` contains the OpenCode subagent markdown files
- each team `README.md` explains roles, workflow, permissions, and usage examples
- `reference-agents/` contains the original standalone/reference agent markdown files used for comparison, sourcing, or future pack building

## Notes

- These templates are designed as custom OpenCode specialist-agent packs; most agents are subagents
- `agents-orchestrator` in each pack now defaults to `mode: all`, so it can be used as both a top-level agent and a callable coordinator
- In this setup, orchestrator delegation and `permission.task` should use each agent's declared markdown `name:` value, not the filename stem
- If you use a team pack as a live OpenCode agents directory, confirm your setup supports loading agents from the nested `agents/` subdirectory
