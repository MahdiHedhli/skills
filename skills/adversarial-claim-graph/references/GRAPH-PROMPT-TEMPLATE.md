# {{PROJECT}} {{PHASE}}
## {{MISSION_TITLE}}

# MISSION

{{OBJECTIVE}}

Do not perform the final human-gated action in this phase.

Repository evidence is authoritative.

Git outranks this prompt.

---

# A. GRAPH CONTROL PLANE

Maintain:

1. `{{slug}}-graph-state.json`
2. `{{slug}}-claim-ledger.json`
3. `{{slug}}-challenge-ledger.json`
4. `{{slug}}-support-ledger.json`
5. `{{slug}}-arbiter-ledger.json`
6. one node receipt per completed node
7. one authority manifest

Exactly one node may be `RUNNING`.

Resume from the first non-PASS node whose dependencies remain exact.

---

# B. STARTING AUTHORITY

- branch: `{{branch}}`
- expected head: `{{head}}`
- expected tree: `{{tree}}`
- prior accepted authority: `{{prior_authority}}`
- historical ledger or invariant: `{{ledger}}`

Bootstrap must verify:

- fresh fetch
- ancestry
- parity
- clean worktree
- ownership and locks
- prior graph state
- no conflicting active loop
- no already-consumed one-shot authority

---

# C. HARD INVARIANTS

{{hard_invariants}}

---

# D. CLAIM PROTOCOL

Every readiness-critical claim includes:

- claim ID
- falsifiable statement
- dependencies
- proof artifacts
- tests
- challenges
- support responses
- arbiter verdict
- invalidated nodes

Allowed arbiter verdicts:

- `ACCEPT`
- `REJECT`
- `UNRESOLVED`

Global acceptance requires every readiness-critical claim to be `ACCEPT`.

---

# E. ROLES

Builder:

`{{builder}}`

Challenger:

`{{challenger}}`

Arbiter:

`{{arbiter}}`

The challenger creates challenge rows.

The builder responds through evidence, repair, concession, or unresolved status.

The arbiter decides each readiness-critical claim.

---

# F. GRAPH TOPOLOGY

```text
{{topology}}
```

---

# G. NODE DEFINITIONS

## {{NODE_ID}}. {{NODE_TITLE}}

### Inputs

{{node_inputs}}

### Work

{{node_work}}

### Prohibited

{{node_prohibited}}

### Proof

{{node_proof}}

### Claims

{{node_claims}}

### Exit

{{node_exit}}

### Failure routing

{{node_failure_routing}}

Repeat for every node.

---

# H. REPAIR AND INVALIDATION

When a finding arrives:

1. map it to a claim
2. identify the earliest invalidated node
3. repair the smallest truthful surface
4. add regression coverage
5. rerun only the invalidated subgraph
6. rerun exact-head CI for execution-byte changes
7. preserve historical evidence append-only
8. resubmit changed claims and their transitive dependencies

Do not rerun immutable one-shot execution after it completes.

---

# I. REVIEW PACKETS

Challenge packet:

- authority manifest
- active claims
- implementation diff
- test and mutation index
- exact review questions

Arbiter packet:

- final authority manifest
- claim ledger
- challenge ledger
- support ledger
- exact-head CI
- changed claims
- invalidation map

---

# J. STOP RULES

Do not stop for repairable implementation, validation, CI, or reviewer findings while budget remains.

Stop for:

- irreconcilable authority conflict
- unauthorized access requirement
- out-of-scope semantic change
- exhausted review budget
- unresolved readiness-critical claim
- final human gate

---

# K. NOTIFICATIONS

{{notifications}}

---

# L. COMMIT DISCIPLINE

- inspect status and diff
- stage exact paths only
- never use broad add commands
- batch pushes at authority, CI, and review boundaries
- no force push
- no history rewrite
- evidence-only pushes must not trigger expensive implementation jobs

---

# M. FINAL RESPONSE

Return:

1. authority reconciliation
2. graph node results
3. claim ledger summary
4. challenge summary
5. support summary
6. arbiter verdicts
7. CI and evidence
8. safety state
9. exact verdict
10. readiness
11. next human-gated action
