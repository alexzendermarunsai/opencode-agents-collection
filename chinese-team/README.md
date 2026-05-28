# Chinese Team

A heterogeneous Chinese-model OpenCode agent template based on the lean `a-team` workflow.

Use `chinese-team` when you want the same 11-agent product-delivery roster as `a-team`, but with model routing split across Qwen, DeepSeek, and GLM through the `opencode-go` provider. It keeps the lean planning, discovery, design, implementation, validation, and documentation flow while assigning each work lane to the Chinese model family best suited for it.

## How It Differs From `a-team`

- Same lean 11-agent roster as `a-team`
- Same overall workflow shape, role boundaries, and permission model
- Different model routing:
  - Qwen coordinates orchestration
  - DeepSeek handles code-heavy implementation and architecture work
  - GLM handles planning, research, design, validation, and documentation work
- No extra deployment, performance, security, accessibility, AI, or prototype specialists from `a-team-plus`

Choose this pack when the lean `a-team` workflow fits and you want Chinese-model routing rather than a single-model or GPT/DeepSeek-only variant.

## Model Routing

| Work lane | Agents | Model |
| --- | --- | --- |
| Orchestration | `Agents Orchestrator` | `opencode-go/qwen3.7-max` |
| Coding and architecture | `Senior Developer`, `Frontend Developer`, `Backend Architect` | `opencode-go/deepseek-v4-pro` |
| Planning, research, design, validation, and docs | `Senior Project Manager`, `UX Researcher`, `UX Architect`, `UI Designer`, `API Tester`, `Reality Checker`, `Technical Writer` | `opencode-go/glm-5.1` |

## Structure

- `agents/` contains the agent markdown files
- `README.md` explains the template, roles, workflow, model routing, and usage

## Agent Roles

- `agents/agents-orchestrator.md` - coordinates multi-agent delivery and routes work to the right specialists
- `agents/senior-project-manager.md` - turns requests into scoped execution plans and task breakdowns
- `agents/ux-researcher.md` - synthesizes user evidence, highlights uncertainty, and supports discovery work
- `agents/ux-architect.md` - defines structure, flows, layout systems, and implementation-ready UX foundations
- `agents/ui-designer.md` - defines visual language, component styling, and implementation-ready UI direction
- `agents/frontend-developer.md` - builds accessible, responsive frontend experiences
- `agents/backend-architect.md` - designs and implements backend systems, APIs, and data models
- `agents/senior-developer.md` - owns complex cross-layer implementation when one strong full-stack owner is useful
- `agents/api-tester.md` - validates API behavior, contracts, and release risks
- `agents/reality-checker.md` - performs skeptical final validation based on available evidence
- `agents/technical-writer.md` - writes and improves docs that match what was actually built

## Suggested Workflow

For a balanced product feature request, a typical flow is:

1. `senior-project-manager`
2. optional `ux-researcher`
3. `ux-architect`
4. optional `ui-designer`
5. `frontend-developer` and/or `backend-architect`
6. `senior-developer` instead of split implementation when one cross-layer owner is better
7. `api-tester` when API risk exists
8. `reality-checker`
9. `technical-writer` when docs need to change

The orchestrator should preserve these quality gates while routing specialist work according to the model table above.

## OpenCode Agent Type

These files define custom OpenCode specialist agents. Most are subagents, and `agents-orchestrator` defaults to `mode: all` so it can work as both a selectable top-level agent and a callable coordinator.

- Most agents in this template use `mode: subagent`
- `agents-orchestrator` uses `mode: all`
- You can invoke specialists directly with `@agent-id`
- Your normal OpenCode primary agent remains the top-level session owner

In practice:

- Use your normal primary agent for the main session, or select `agents-orchestrator` directly as the top-level agent
- Call `@agents-orchestrator` when you want coordinated multi-agent routing from another agent
- Call a specialist like `@frontend-developer` or `@ux-researcher` when you already know the right role

## Permission Model

This template uses OpenCode `permission` settings instead of the legacy `tools` booleans.

- Planning and design roles are mostly read-only
- Implementation roles can edit files and run bash with approval
- Validation roles cannot edit files, but can run bash with approval when verification is needed
- Research and documentation roles may allow `webfetch` when external references are useful

Current defaults in this template:

- Read-only: `senior-project-manager`, `ux-architect`, `ui-designer`
- Read-only with optional web access: `ux-researcher`
- Edit + bash on approval: `frontend-developer`, `backend-architect`, `senior-developer`
- Validation with bash on approval: `reality-checker`, `agents-orchestrator`
- Validation with bash on approval and optional web access: `api-tester`
- Edit without bash, optional web access: `technical-writer`

If you want a stricter or looser setup, adjust each agent's frontmatter `permission` block or install with `scripts/agents_sync.py --mode safe`, `trusted`, or `yolo`.

## Using in OpenCode

Example local config layout:

```text
.opencode/
  agents/
    agents-orchestrator.md
    senior-project-manager.md
    ux-researcher.md
    ux-architect.md
    ui-designer.md
    frontend-developer.md
    backend-architect.md
    senior-developer.md
    api-tester.md
    reality-checker.md
    technical-writer.md
```

Typical ways to use these subagents in OpenCode:

- Put the agent files in your project-level `.opencode/agents/` directory or your global OpenCode agents directory
- Start with `@agents-orchestrator` when you want one agent to coordinate the rest of the team
- Call a specialist directly when you already know the right role

You can also install the pack with the portable sync script:

```bash
python3 scripts/agents_sync.py sync --pack chinese-team --target ~/.config/opencode/agents
```

## Prompt Examples

Use the orchestrator for a full feature workflow:

```text
@agents-orchestrator Add a team settings page where admins can invite members, change roles, and remove access. Plan the work, use the right specialists, validate the API behavior, and finish with any docs updates needed.
```

Because `agents-orchestrator` defaults to `mode: all`, you can also select it as your top-level agent and use the same kind of prompt without the `@agents-orchestrator` mention:

```text
Add a team settings page where admins can invite members, change roles, and remove access. Plan the work, use the right specialists, validate the API behavior, and finish with any docs updates needed.
```

Use a coding specialist directly:

```text
@senior-developer Implement the account security workflow across the frontend and API, using the existing patterns and adding validation coverage for the main failure paths.
```

Use a GLM-routed specialist directly for planning or documentation:

```text
@technical-writer Update the setup guide so it matches the new onboarding flow, including prerequisites, expected outputs, and troubleshooting notes.
```

## Notes

- The folder name is just a template label; the agent prompts are written to be reusable outside this directory.
- In this setup, orchestrator delegation and `permission.task` should use the declared markdown `name:` values, not the filename stems.
- If you use this as a live OpenCode agents directory, confirm your setup supports loading agents from the `agents/` subdirectory.
- This pack assumes the `opencode-go` provider exposes `qwen3.7-max`, `deepseek-v4-pro`, and `glm-5.1` under the model IDs shown above.
