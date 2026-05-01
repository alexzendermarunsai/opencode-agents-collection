# A-Team for DeepSeek v4 Pro

A DeepSeek v4 Pro-optimized variant of `a-team` for planning, discovery, design, implementation, validation, and documentation.

## What It Is

`a-team-deepseekv4-pro` keeps the same specialist agent roster as `a-team`, but retargets the agents to DeepSeek v4 Pro and adds concise DeepSeek-oriented operating guidance.

## How It Differs From A-Team

- the specialist roster and intent match `a-team`
- the main difference is DeepSeek v4 Pro operating guidance across the agents, including orchestration behavior
- the README and pack framing position this as the `a-team` choice when DeepSeek v4 Pro is your primary model

If you want the same lean workflow without model-specific positioning, use `a-team`.

## When To Choose It

Use `a-team-deepseekv4-pro` when:

- you want the lean `a-team` specialist set retargeted to DeepSeek v4 Pro
- DeepSeek v4 Pro is your primary model
- the leaner `a-team` workflow fits, and model-specific structured-output and evidence-handling guidance is the main differentiator

Use `a-team` when you want the same specialist coverage in the non-model-specific pack.

## Structure

- `agents/` contains the agent markdown files
- `README.md` explains the template, roles, workflow, and usage

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

## Choosing Agent Mode

This template is built around specialist agents, with one orchestrator that can act as both a primary-style entrypoint and a subagent.

- Most files here use `mode: subagent`
- `agents-orchestrator` defaults to `mode: all`
- Keep `mode: all` when you want it usable as both a selectable top-level agent and a callable coordinator
- Use `mode: primary` only if you want orchestration to be the default top-level experience and do not need it to behave as a helper specialist

Practical guidance:

- Reusable template for others -> the current default `mode: all` is a good fit if you want flexibility
- Personal day-to-day workflow -> keep `agents-orchestrator` as `all`

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

If you want a stricter or looser setup, adjust each agent's frontmatter `permission` block.

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
- Start with `@agents-orchestrator` when you want one agent to coordinate the rest of the team.
- Call a specialist directly when you already know the right role.

## Prompt Examples

Use the orchestrator for a full feature workflow:

```text
@agents-orchestrator Add a team settings page where admins can invite members, change roles, and remove access. Plan the work, use the right specialists, validate the API behavior, and finish with any docs updates needed.
```

Because `agents-orchestrator` defaults to `mode: all`, you can also select it as your top-level agent and use the same kind of prompt without the `@agents-orchestrator` mention:

```text
Add a team settings page where admins can invite members, change roles, and remove access. Plan the work, use the right specialists, validate the API behavior, and finish with any docs updates needed.
```

Use a specialist directly for planning:

```text
@senior-project-manager Turn this feature request into a scoped execution plan with clear acceptance criteria and dependencies.
```

Use a specialist directly for UX discovery:

```text
@ux-researcher Review these support tickets and summarize the most likely usability issues, confidence level, and recommended next actions.
```

Use a specialist directly for implementation:

```text
@frontend-developer Implement the account security panel using the existing design system, including loading, empty, success, and error states.
```

## Notes

- The folder name is just a template label; the agent prompts are written to be reusable outside this directory.
- In this setup, orchestrator delegation and `permission.task` should use the declared markdown `name:` values, not the filename stems.
- If you use this as a live OpenCode agents directory, confirm your setup supports loading agents from the `agents/` subdirectory.
- `model: opencode-go/deepseek-v4-pro` is the OpenCode Go provider/model ID for DeepSeek V4 Pro. OpenCode exposes DeepSeek V4 Pro variants (`low`, `medium`, `high`, and `max`); this pack uses the OpenCode `variant:` frontmatter field to select role-appropriate variants and does not set raw `reasoningEffort` directly.
