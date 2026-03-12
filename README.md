# A-Team

A balanced OpenCode agent template for planning, discovery, design, implementation, validation, and documentation.

## Structure

- `agents/` contains the agent markdown files
- `README.md` explains the template, roles, and suggested workflow

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

## Notes

- The folder name is just a template label; the agent prompts are written to be reusable outside this directory.
- If you use this as a live OpenCode agents directory, confirm your setup supports loading agents from the `agents/` subdirectory.

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

Typical ways to use this set in OpenCode:

- Put the agent files in your project-level `.opencode/agents/` directory or your global OpenCode agents directory.
- Start with `@agents-orchestrator` when you want one agent to coordinate the rest of the team.
- Call a specialist directly when you already know the right role.

## Prompt Examples

Use the orchestrator for a full feature workflow:

```text
@agents-orchestrator Add a team settings page where admins can invite members, change roles, and remove access. Plan the work, use the right specialists, validate the API behavior, and finish with any docs updates needed.
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
