# `robogears/overnight-protocol`

Status: not started.

## To investigate (inspect actual repo/implementation, not just README)

Same general list as `autonomous-loop.md` (workflow, task breakdown, state
persistence, resumption, crash handling, git/checkpointing, verification,
continue/stop/retry/escalate logic, and where its orchestration overhead is
or isn't justified) **plus** a deep dive on its permission model:

- What is automatically permitted.
- What is explicitly denied (inspect the actual deny rules, not a summary).
- What can still cause an interruption despite the deny rules.
- Which protections are enforced by Claude Code itself vs. which are merely
  instructions to Claude (i.e., convention, not a hard boundary).
- What `--dangerously-skip-permissions` specifically changes.
- What the deny rules still protect against under that flag.
- Gaps.
- Particularly useful rules.
- Particularly restrictive/annoying rules.
- Whether an adapted subset would improve ordinary Claude Code usage outside
  of an AFK-style workflow.

## Findings

(none yet)
