# Adoption Guide

## Use in a new project

1. Copy this skill into the agent's skills directory or upload the ZIP.
2. Start with `DESIGN` mode.
3. Supply the project handoff, authority rules, final human gate, reviewers, and notification channel.
4. Generate a project-specific Markdown graph prompt.
5. Commit graph state and ledgers only when the project requires repository durability.

## Use in an existing long-running thread

1. Treat the latest committed evidence as the starting authority.
2. Convert prior work into completed nodes and accepted or rejected claims.
3. Set the active frontier to the smallest unresolved boundary.
4. Preserve old linear prompts as historical references.
5. Do not replay completed execution solely to conform to the new structure.

## Naming

Recommended skill invocation phrases:

- "Build an adversarial claim graph for this phase."
- "Convert this handoff into a resumable graph prompt."
- "Resume the claim graph from the latest committed node."
- "Audit this graph's readiness claims."
- "Create an overnight graph loop with challenger and arbiter review."

## Project-specific extensions

Add fields when needed for:

- ledger accounting
- checkpoint access
- deployment authority
- regulated data
- financial or legal review
- experiment preregistration
- notification milestones
- model and reviewer identity
- one-shot execution tokens

Keep the generic claim and invalidation protocol unchanged.
