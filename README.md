# A-Team Plus

A comprehensive OpenCode agent template for planning, discovery, design, implementation, validation, deployment, performance, security, accessibility, AI work, and documentation.

## How It Differs From A-Team

`a-team` is the lean, balanced core.

`a-team-plus` adds broader shipping and specialty coverage:

- deployment and CI/CD via `devops-automator`
- performance validation via `performance-benchmarker`
- security review via `security-engineer`
- accessibility review via `accessibility-auditor`
- AI feature implementation via `ai-engineer`
- fast MVP and prototype work via `rapid-prototyper`

Use `a-team-plus` when the work goes beyond product delivery and includes release operations, non-functional review, AI integration, or rapid concept validation.

## Structure

- `agents/` contains the agent markdown files
- `README.md` explains the template, roles, workflow, permissions, and usage

## Agent Roles

- `agents/agents-orchestrator.md` - coordinates multi-agent delivery and routes work to the right specialists
- `agents/senior-project-manager.md` - turns requests into scoped execution plans and task breakdowns
- `agents/ux-researcher.md` - synthesizes user evidence, highlights uncertainty, and supports discovery work
- `agents/ux-architect.md` - defines structure, flows, layout systems, and implementation-ready UX foundations
- `agents/ui-designer.md` - defines visual language, component styling, and implementation-ready UI direction
- `agents/frontend-developer.md` - builds accessible, responsive frontend experiences
- `agents/backend-architect.md` - designs and implements backend systems, APIs, and data models
- `agents/senior-developer.md` - owns complex cross-layer implementation when one strong full-stack owner is useful
- `agents/rapid-prototyper.md` - builds fast validation-focused MVPs and proofs of concept
- `agents/ai-engineer.md` - implements model-backed features, inference workflows, and AI integration
- `agents/api-tester.md` - validates API behavior, contracts, and release risks
- `agents/performance-benchmarker.md` - benchmarks performance, identifies bottlenecks, and assesses scalability risk
- `agents/security-engineer.md` - reviews security risk, hardening needs, and release blockers
- `agents/accessibility-auditor.md` - reviews accessibility barriers and inclusive release readiness
- `agents/devops-automator.md` - handles deployment automation, CI/CD, environment management, and release operations
- `agents/reality-checker.md` - performs skeptical final validation based on available evidence
- `agents/technical-writer.md` - writes and improves docs that match what was actually built

## Suggested Workflow

For a comprehensive feature or release workflow, a typical flow is:

1. `senior-project-manager`
2. optional `ux-researcher`
3. optional `rapid-prototyper` when the goal is fast validation before full build-out
4. `ux-architect`
5. optional `ui-designer`
6. `frontend-developer` and/or `backend-architect`
7. `senior-developer` instead of split implementation when one cross-layer owner is better
8. `ai-engineer` when the feature includes model-backed behavior
9. `api-tester`
10. optional `performance-benchmarker`
11. optional `security-engineer`
12. optional `accessibility-auditor`
13. optional `devops-automator`
14. `reality-checker`
15. `technical-writer` when docs need to change

## OpenCode Agent Type

These files define custom OpenCode specialist agents. Most are subagents, and `agents-orchestrator` defaults to `mode: all` so it can work as both a selectable top-level agent and a callable coordinator.

- Most agents in this template use `mode: subagent`
- `agents-orchestrator` uses `mode: all`
- You can invoke specialists directly with `@agent-id`
- Your normal OpenCode primary agent remains the top-level session owner

In practice:

- Use your normal primary agent for the main session, or select `agents-orchestrator` directly as the top-level agent
- Call `@agents-orchestrator` when you want coordinated multi-agent routing from another agent
- Call a specialist directly when you already know the right role

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
- Validation and audit roles cannot edit files, but can run bash with approval when verification is needed
- Research, documentation, and AI-oriented roles may allow `webfetch` when external references are useful

Current defaults in this template:

- Read-only: `senior-project-manager`, `ux-architect`, `ui-designer`
- Read-only with optional web access: `ux-researcher`
- Edit + bash on approval: `frontend-developer`, `backend-architect`, `senior-developer`, `devops-automator`, `rapid-prototyper`
- Edit + bash on approval and optional web access: `ai-engineer`
- Validation with bash on approval: `reality-checker`, `agents-orchestrator`, `performance-benchmarker`, `security-engineer`, `accessibility-auditor`
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
    rapid-prototyper.md
    ai-engineer.md
    api-tester.md
    performance-benchmarker.md
    security-engineer.md
    accessibility-auditor.md
    devops-automator.md
    reality-checker.md
    technical-writer.md
```

Typical ways to use these subagents in OpenCode:

- Put the agent files in your project-level `.opencode/agents/` directory or your global OpenCode agents directory
- Start with `@agents-orchestrator` when you want one agent to coordinate the full expanded team
- Call a specialist directly when you already know the right role

## Prompt Examples

Use the orchestrator for a full shipping workflow:

```text
@agents-orchestrator Build an AI-assisted support triage feature, plan the work, use the right specialists, validate API and accessibility risks, check security and performance concerns, prepare deployment changes, and finish with any docs updates needed.
```

Because `agents-orchestrator` defaults to `mode: all`, you can also select it as your top-level agent and use the same kind of prompt without the `@agents-orchestrator` mention:

```text
Build an AI-assisted support triage feature, plan the work, use the right specialists, validate API and accessibility risks, check security and performance concerns, prepare deployment changes, and finish with any docs updates needed.
```

Use a specialist directly for deployment work:

```text
@devops-automator Set up a safer deployment workflow for this app with CI checks, environment configuration review, and rollback guidance.
```

Use a specialist directly for performance review:

```text
@performance-benchmarker Review the checkout flow and API latency, identify the biggest bottlenecks, and recommend the highest-leverage fixes.
```

Use a specialist directly for fast validation:

```text
@rapid-prototyper Build the smallest testable version of this onboarding idea so we can validate the main user flow quickly.
```

## Notes

- The folder name is just a template label; the agent prompts are written to be reusable outside this directory.
- In this setup, orchestrator delegation and `permission.task` should use the declared markdown `name:` values, not the filename stems.
- If you use this as a live OpenCode agents directory, confirm your setup supports loading agents from the `agents/` subdirectory.
