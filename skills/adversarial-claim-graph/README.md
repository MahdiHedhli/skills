# Adversarial Claim Graph

A portable skill for long-horizon, evidence-backed engineering and research workflows.

It complements `graph-engineering`: dependency graphs optimize work shape and parallelism, while this skill manages durable authority, falsifiable claims, adversarial review, incremental repair, and human-gated execution.

## Contents

- `SKILL.md`: activation and execution instructions
- `references/GRAPH-PROMPT-TEMPLATE.md`: generic graph prompt skeleton
- `references/CLAIM-PROTOCOL.md`: claim, challenge, support, and arbiter rules
- `references/REVIEW-PACKET.md`: compact adversarial-review packet format
- `references/ADOPTION-GUIDE.md`: installation and migration guidance
- `references/WORKED-EXAMPLE.md`: fictional one-shot release-gate example
- `scripts/validate_graph_state.py`: standard-library validator

## Validation

```bash
python3 skills/adversarial-claim-graph/scripts/validate_graph_state.py /path/to/graph-artifacts
```

The validator expects files named:

- `graph-state.json`
- `claim-ledger.json`
- `challenge-ledger.json`
- `support-ledger.json`
- `arbiter-ledger.json`

Project-specific names can be copied or symlinked into a validation directory.
