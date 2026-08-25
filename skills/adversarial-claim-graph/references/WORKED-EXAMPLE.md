# Worked Example: One-Shot Release Migration Gate

This fictional example demonstrates the graph style without binding it to a real person, repository, company, product, service, or dataset.

## Mission

Prepare one irreversible production migration, prove readiness through an independent challenger and arbiter, and stop before the human `GO`.

## Hard invariants

- production migration executed: no
- live authorization created: no
- source data modified: no
- rollback package prepared: yes
- human GO required: yes

## Graph

```text
R0 AUTHORITY_RECONCILIATION
  |
  v
R1 MIGRATION_CONTRACT
  |
  v
R2 DRY_RUN_AND_ROLLBACK_PROOF
  |
  v
R3 EXACT_HEAD_CI
  |
  v
R4 CHALLENGE
  |
  v
R5 SUPPORT_AND_REPAIR
  |
  v
R6 ARBITER
  |
  +-- REJECT/UNRESOLVED --> earliest invalidated node
  |
  +-- ACCEPT -----------> R7 FINAL_READINESS
  |
  v
STOP_AT_HUMAN_GO
```

## Example claims

`C-REF-001`

> The selected release branch is the only authoritative lineage.

`C-DATA-001`

> Every source record maps to exactly one target record or one declared rejection class.

`C-ROLLBACK-001`

> The rollback package restores the pre-migration state without relying on mutable external state.

`C-GATE-001`

> No production write can occur before the human GO artifact exists.

## Challenge example

The challenger mutates one mapping rule so two source records collide in the target. The dry-run validator must reject the package and invalidate R2 and all dependent nodes.

## Support example

The builder adds a uniqueness proof, a collision mutation, and a deterministic replay test. The support row binds the repair commit and rerun evidence.

## Arbiter example

The arbiter independently evaluates every readiness-critical claim and returns:

- C-REF-001: ACCEPT
- C-DATA-001: ACCEPT
- C-ROLLBACK-001: ACCEPT
- C-GATE-001: ACCEPT
- global verdict: ACCEPT

## Final state

`READY_FOR_ONE_SHOT_MIGRATION_GO: YES`

`PRODUCTION_MIGRATION_EXECUTED: NO`

The workflow stops and requests a fresh human GO.
