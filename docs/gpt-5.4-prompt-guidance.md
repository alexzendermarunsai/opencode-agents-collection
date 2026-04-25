# GPT-5.4 prompting guide

Source: https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.4

## GPT-5.4 prompting guide

### New in GPT-5.4 vs GPT-5.2

- Stronger long-running task performance with more reliable multi-step execution.
- Better control over style, tone, and structured output contracts.
- More disciplined tool persistence, verification loops, and evidence-grounded synthesis.
- Small-model notes for `gpt-5.4-mini` and `gpt-5.4-nano`.

GPT-5.4, our newest mainline model, is designed to balance long-running task performance, stronger control over style and behavior, and more disciplined execution across complex workflows. Building on advances from GPT-5 through GPT-5.3-Codex, GPT-5.4 improves token efficiency, sustains multi-step workflows more reliably, and performs well on long-horizon tasks.

GPT-5.4 is designed for production-grade assistants and agents that need strong multi-step reasoning, evidence-rich synthesis, and reliable performance over long contexts. It is especially effective when prompts clearly specify the output contract, tool-use expectations, and completion criteria. In practice, the biggest gains come from choosing the right reasoning effort for the task, using explicit grounding and citation rules, and giving the model a precise definition of what “done” looks like. This guide focuses on prompt patterns and migration practices that preserve those efficiency wins. For model capabilities, API parameters, and broader migration guidance, see the latest model guide.

When troubleshooting cases where GPT-5.4 treats an intermediate update as the final answer, verify your integration preserves the assistant message `phase` field correctly. See Phase parameter for details.

## Understand GPT-5.4 behavior

### Where GPT-5.4 is strongest

GPT-5.4 tends to work especially well in these areas:

- Strong personality and tone adherence, with less drift over long answers
- Agentic workflow robustness, with a stronger tendency to stick with multi-step work, retry, and complete agent loops end to end
- Evidence-rich synthesis, especially in long-context or multi-tool workflows
- Instruction adherence in modular, skill-based, and block-structured prompts when the contract is explicit
- Long-context analysis across large, messy, or multi-document inputs
- Batched or parallel tool calling while maintaining tool-call accuracy
- Spreadsheet, finance, and Excel workflows that need instruction following, formatting fidelity, and stronger self-verification

### Where explicit prompting still helps

Even with those strengths, GPT-5.4 benefits from more explicit guidance in a few recurring patterns:

- Low-context tool routing early in a session, when tool selection can be less reliable
- Dependency-aware workflows that need explicit prerequisite and downstream-step checks
- Reasoning effort selection, where higher effort is not always better and the right choice depends on task shape, not intuition
- Research tasks that require disciplined source collection and consistent citations
- Irreversible or high-impact actions that require verification before execution
- Terminal or coding-agent environments where tool boundaries must stay clear

These patterns are observed defaults, not guarantees. Start with the smallest prompt that passes your evals, and add blocks only when they fix a measured failure mode.

## Use core prompt patterns

### Keep outputs compact and structured

To improve token efficiency with GPT-5.4, constrain verbosity and enforce structured output through clear output contracts. In practice, this acts as an additional control layer alongside the `verbosity` parameter in the Responses API, allowing you to guide both how much the model writes and how it structures the output.

```text
<output_contract>
- Return exactly the sections requested, in the requested order.
- If the prompt defines a preamble, analysis block, or working section, do not treat it as extra output.
- Apply length limits only to the section they are intended for.
- If a format is required (JSON, Markdown, SQL, XML), output only that format.
</output_contract>

<verbosity_controls>
- Prefer concise, information-dense writing.
- Avoid repeating the user's request.
- Keep progress updates brief.
- Do not shorten the answer so aggressively that required evidence, reasoning, or completion checks are omitted.
</verbosity_controls>
```

### Set clear defaults for follow-through

Users often change the task, format, or tone mid-conversation. To keep the assistant aligned, define clear rules for when to proceed, when to ask, and how newer instructions override earlier defaults.

Use a default follow-through policy like this:

```text
<default_follow_through_policy>
- If the user’s intent is clear and the next step is reversible and low-risk, proceed without asking.
- Ask permission only if the next step is:
  (a) irreversible,
  (b) has external side effects (for example sending, purchasing, deleting, or writing to production), or
  (c) requires missing sensitive information or a choice that would materially change the outcome.
- If proceeding, briefly state what you did and what remains optional.
</default_follow_through_policy>
```

Make instruction priority explicit:

```text
<instruction_priority>
- User instructions override default style, tone, formatting, and initiative preferences.
- Safety, honesty, privacy, and permission constraints do not yield.
- If a newer user instruction conflicts with an earlier one, follow the newer instruction.
- Preserve earlier instructions that do not conflict.
</instruction_priority>
```

Higher-priority developer or system instructions remain binding.

Guidance: When instructions change mid-conversation, make the update explicit, scoped, and local. State what changed, what still applies, and whether the change affects the next turn or the rest of the conversation.

### Handle mid-conversation instruction updates

For mid-conversation updates, use explicit, scoped steering messages that state:

1. Scope
2. Override
3. Carry forward

```text
<task_update>
For the next response only:
- Do not complete the task.
- Only produce a plan.
- Keep it to 5 bullets.

All earlier instructions still apply unless they conflict with this update.
</task_update>
```

If the task itself changes, say so directly:

```text
<task_update>
The task has changed.
Previous task: complete the workflow.
Current task: review the workflow and identify risks only.

Rules for this turn:
- Do not execute actions.
- Do not call destructive tools.
- Return exactly:
  1. Main risks
  2. Missing information
  3. Recommended next step
</task_update>
```

### Make tool use persistent when correctness depends on it

Use explicit rules to keep tool use thorough, dependency-aware, and appropriately paced, especially in workflows where later actions rely on earlier retrieval or verification. A common failure mode is skipping prerequisites because the right end state seems obvious.

GPT-5.4 can be less reliable at tool routing early in a session, when context is still thin. Prompt for prerequisites, dependency checks, and exact tool intent.

```text
<tool_persistence_rules>
- Use tools whenever they materially improve correctness, completeness, or grounding.
- Do not stop early when another tool call is likely to materially improve correctness or completeness.
- Keep calling tools until:
  (1) the task is complete, and
  (2) verification passes (see <verification_loop>).
- If a tool returns empty or partial results, retry with a different strategy.
</tool_persistence_rules>
```

This is especially important for workflows where the final action depends on earlier lookup or retrieval steps. One of the most common failure modes is skipping prerequisites because the intended end state seems obvious.

```text
<dependency_checks>
- Before taking an action, check whether prerequisite discovery, lookup, or memory retrieval steps are required.
- Do not skip prerequisite steps just because the intended final action seems obvious.
- If the task depends on the output of a prior step, resolve that dependency first.
</dependency_checks>
```

Prompt for parallelism when the work is independent and wall-clock matters. Prompt for sequencing when dependencies, ambiguity, or irreversible actions matter more than speed.

```text
<parallel_tool_calling>
- When multiple retrieval or lookup steps are independent, prefer parallel tool calls to reduce wall-clock time.
- Do not parallelize steps that have prerequisite dependencies or where one result determines the next action.
- After parallel retrieval, pause to synthesize the results before making more calls.
- Prefer selective parallelism: parallelize independent evidence gathering, not speculative or redundant tool use.
</parallel_tool_calling>
```

### Force completeness on long-horizon tasks

For multi-step workflows, a common failure mode is incomplete execution: the model finishes after partial coverage, misses items in a batch, or treats empty or narrow retrieval as final. GPT-5.4 becomes more reliable when the prompt defines explicit completion rules and recovery behavior.

Coverage can be achieved through sequential or parallel retrieval, but completion rules should remain explicit either way.

```text
<completeness_contract>
- Treat the task as incomplete until all requested items are covered or explicitly marked [blocked].
- Keep an internal checklist of required deliverables.
- For lists, batches, or paginated results:
  - determine expected scope when possible,
  - track processed items or pages,
  - confirm coverage before finalizing.
- If any item is blocked by missing data, mark it [blocked] and state exactly what is missing.
</completeness_contract>
```

For workflows where empty, partial, or noisy retrieval is common:

```text
<empty_result_recovery>
If a lookup returns empty, partial, or suspiciously narrow results:
- do not immediately conclude that no results exist,
- try at least one or two fallback strategies,
  such as:
  - alternate query wording,
  - broader filters,
  - a prerequisite lookup,
  - or an alternate source or tool,
- Only then report that no results were found, along with what you tried.
</empty_result_recovery>
```

### Add a verification loop before high-impact actions

Once the workflow appears complete, add a lightweight verification step before returning the answer or taking an irreversible action. This helps catch requirement misses, grounding issues, and format drift before commit.
