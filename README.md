# OpenCode Agents Collection

This repository contains reusable OpenCode specialist-agent templates organized into curated team packs and standalone reference agents.

For normal day-to-day use, sync a curated pack into your live OpenCode agents directory with `scripts/agents_sync.py` instead of pointing OpenCode at this repo directly.

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

## Portable Sync Script

Use `scripts/agents_sync.py` when you want to install a curated pack into a real OpenCode agents directory outside this repository.

- `sync` installs `a-team` or `a-team-plus` into a user-supplied target directory and writes a manifest/state file there
- `safe` rewrites agent `permission` blocks to a stricter portable baseline; `trusted` installs the authored pack files as-is; `yolo` installs authored files, then rewrites only literal frontmatter `permission` values from `ask` to `allow`
- `status` shows whether the target still matches the last managed install
- `reset` removes only files tracked by the manifest/state file
- `interactive` walks through target selection, status review, action choice, preview, and final confirmation while reusing the same guarded sync/reset/status paths
- `yolo` requires an extra typed `YOLO` confirmation before writes unless you use `--dry-run`, because it removes approval gates for risky actions in the target install
- the source repo stays read-only during normal use, and the script never installs anything from `reference-agents/`
- target-directory drift, missing managed files, or unmanaged filename conflicts block `sync` and `reset` unless you rerun with `--force`
- `--dry-run` prints planned actions without changing the target directory

See `scripts/agents-sync.md` for examples and command details.

## Notes

- These templates are designed as custom OpenCode specialist-agent packs; most agents are subagents
- `agents-orchestrator` in each pack now defaults to `mode: all`, so it can be used as both a top-level agent and a callable coordinator
- In this setup, orchestrator delegation and `permission.task` should use each agent's declared markdown `name:` value, not the filename stem
- If you use a team pack as a live OpenCode agents directory, confirm your setup supports loading agents from the nested `agents/` subdirectory
- If you want a separate live agents directory outside this repo, prefer `scripts/agents_sync.py` over copying files by hand
