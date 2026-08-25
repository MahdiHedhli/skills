# Claim Protocol Reference

## Claim

A claim is a falsifiable load-bearing statement, not a summary sentence.

Required fields:

- `claim_id`
- `statement`
- `scope`
- `introduced_by_node`
- `depends_on`
- `proof_artifacts`
- `test_evidence`
- `challenge_status`
- `support_status`
- `arbiter_verdict`
- `invalidates_nodes`
- `readiness_critical`
- `status`

## Challenge

A challenge attacks one claim.

Required fields:

- `challenge_id`
- `claim_id`
- `attack`
- `mutation_or_trace`
- `expected_behavior`
- `observed_behavior`
- `severity`
- `affected_artifacts`
- `status`

## Support

A support row answers one challenge.

Allowed dispositions:

- `ANSWERED_BY_EXISTING_EVIDENCE`
- `REPAIR_IMPLEMENTED`
- `CLAIM_CONCEDED`
- `UNRESOLVED`

Required fields:

- `support_id`
- `challenge_id`
- `disposition`
- `evidence`
- `repair_commit`
- `tests`
- `remaining_uncertainty`

## Arbiter

The arbiter decides each readiness-critical claim:

- `ACCEPT`
- `REJECT`
- `UNRESOLVED`

A global PASS is invalid when any readiness-critical claim is rejected, unresolved, or lacks a verdict.

## Invalidation

Every claim records the earliest nodes invalidated by its failure.

A repair reruns only those nodes and their dependents.

Immutable execution nodes are never rerun after completion.
