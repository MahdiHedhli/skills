---
name: adversarial-claim-graph
description: Design, execute, resume, and review long-horizon engineering or research work as a durable claim graph with authoritative bootstrap, node receipts, claim/challenge/support/arbiter ledgers, bounded repair loops, incremental invalidation, explicit human gates, and evidence-backed final declarations. Use when work spans multiple commits, CI runs, reviewers, one-shot actions, or safety-critical stop boundaries. Do not use for simple one-off tasks.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [graph, workflow, claims, evidence, adversarial-review, resumable, human-gate]
    related_skills: [graph-engineering, scope-first]
---

# Adversarial Claim Graph

Use this skill to turn a long linear prompt into a resumable evidence graph.

The graph is not a decorative checklist. It is the control plane for authority, execution, review, repair, and final human gates.

## Activation

Use this skill when at least one of these is true:

- The task spans several commits, tools, CI runs, or review cycles.
- Repository or committed evidence outranks conversational history.
- Independent adversarial review is required.
- A one-shot action, real data read, deployment, authorization, or expensive execution is human-gated.
- The work may be interrupted and must resume without replaying completed phases.
- A correct unresolved result is preferable to manufactured acceptance.
- Repairs should invalidate only the earliest affected work, not restart everything.

Do not use it for a short rewrite, a simple bug fix, or a task that needs no durable evidence.

## Select the operating mode

Infer one mode:

- `DESIGN`: create a graph prompt from a handoff, objective, and constraints.
- `EXECUTE`: run or resume an existing graph.
- `REVIEW`: audit a graph, its ledgers, and its authority closure.
- `MIGRATE`: convert a long linear prompt into this graph style.

When the user asks for a prompt, produce a downloadable `.md` file by default.

## Core doctrine

1. **Authority first**
   - Resolve the authoritative branch, head, tree, parity, worktree, locks, and prior state before substantive claims.
   - Git, committed bytes, and durable evidence outrank prose.
   - A newer valid authority supersedes a handoff. A divergent authority stops for adjudication.

2. **Persistent control plane**
   - Maintain graph state, claim, challenge, support, and arbiter ledgers.
   - Every completed node has a receipt.
   - Exactly one node may be `RUNNING`.
   - Resume from the active frontier after verifying completed receipts and dependency SHAs.

3. **Claims, not narrative**
   - Turn every load-bearing assertion into a typed claim.
   - Bind each claim to proof artifacts, tests, dependencies, invalidation targets, and readiness criticality.
   - Do not treat a passing outer artifact hash as proof that its internal bindings are correct.

4. **Challenge, support, arbiter**
   - A challenger attacks claims and creates challenge rows.
   - The builder answers with existing evidence, a repair, a concession, or `UNRESOLVED`.
   - An independent arbiter issues `ACCEPT`, `REJECT`, or `UNRESOLVED` per readiness-critical claim.
   - Global acceptance requires explicit arbiter acceptance of every readiness-critical claim.

5. **Incremental invalidation**
   - A repair returns to the earliest node invalidated by the changed claim or byte.
   - Do not replay completed nodes whose dependencies remain exact.
   - After one-shot execution, repairs may change evidence, validators, indexes, or declarations only. Never rerun immutable execution under the same authority.

6. **Constructibility before confidence**
   - Contracts and matrices must describe artifacts that can be serialized in causal order.
   - No artifact may bind its own SHA or a future artifact SHA.
   - When possible, symbolically construct every legal outcome with real canonical bytes and real hashes before implementation review.

7. **Human gates stay human**
   - Preparation may proceed autonomously.
   - Do not mint live authority, access protected data, deploy, submit, or execute a one-shot event without the explicit operator gate.
   - A failed event is evidence, not permission to retry.

8. **Unresolved is legitimate**
   - Never manufacture PASS.
   - A readiness-critical `UNRESOLVED` claim produces NO readiness and a precise smallest blocker.

## Graph control plane

Create these durable artifacts, adapted to repository conventions:

- graph state
- node receipts
- claim ledger
- challenge ledger
- support ledger
- arbiter ledger
- authority manifest
- final reconciliation or declaration

Use the schemas in `assets/` as a starting point.

Run:

```bash
python scripts/validate_graph_state.py /path/to/graph-directory
```

before review and before final acceptance.

## Node design

Each node must declare:

- node ID and purpose
- dependencies
- authoritative inputs
- work allowed
- work prohibited
- proof artifacts
- tests and mutations
- claims introduced or closed
- safety invariants
- exit predicate
- failure routing
- next eligible edges

Prefer 6 to 14 meaningful nodes. Split only at durable authority or review boundaries.

A node passes only when its exit predicate is mechanically supported.

## Claim design

Each load-bearing claim records:

- stable claim ID
- exact statement
- scope
- introducing node
- dependencies
- proof artifacts
- test evidence
- challenge status
- support status
- arbiter verdict
- invalidated nodes
- readiness criticality
- current status

Good claims are falsifiable. Avoid claims such as "the implementation is robust."

Prefer:

> `C-ROOT-002`: Substitution or loss of the primary evidence-root pathname cannot reduce a previously verified durable-start lower bound to zero.

## Reviewer packets

Do not resend the whole project history every cycle.

A reviewer packet should contain:

- authoritative head and tree
- authority manifest
- active graph frontier
- changed claims
- transitive dependency SHAs
- implementation diff from the prior reviewed head
- tests and mutation indexes
- prior challenges and support dispositions
- exact questions the reviewer must decide

The challenger produces challenge rows. The arbiter produces claim verdicts.

## Repair routing

When a finding arrives:

1. Map it to a claim.
2. Identify the earliest invalidated node.
3. Record the invalidation.
4. Repair the smallest truthful surface.
5. Add a permanent regression or mutation.
6. Rerun only the invalidated subgraph.
7. Rerun exact-head CI for execution-byte changes.
8. Update reviewer packets with changed claims and dependencies.
9. Preserve historical rejected artifacts append-only.

## Safety and stop rules

Every graph must define:

- hard invariants
- authorized work
- prohibited work
- repairable stop conditions
- nonrepairable stop conditions
- review and repair budgets
- exact human-gated boundary

Do not make the stop threshold so small that a missing field, validator failure, CI failure, or repairable reviewer rejection ends a long program.

Do stop for:

- irreconcilable authority conflict
- required access outside authorization
- required numerical or semantic scope expansion outside the approved phase
- exhausted review budget
- unresolved readiness-critical claim
- final human gate

## Output defaults

When designing a graph prompt:

1. Save the complete prompt as a downloadable Markdown file.
2. Keep the chat response to a concise purpose statement and link.
3. Give the file a stable descriptive name.
4. Include a final response schema in the prompt.
5. Include notification milestones when the workflow uses a notification channel.
6. Include commit and push discipline when Git is authoritative.

Use `references/GRAPH-PROMPT-TEMPLATE.md`.

## Quality checks

Reject or repair a graph that:

- is only a long linear checklist with graph labels
- repeats full history in every review cycle
- has no persistent ledgers
- has no node receipts
- allows several nodes to be RUNNING
- lacks claim-level arbiter verdicts
- treats unresolved claims as accepted
- reruns immutable one-shot work after evidence defects
- binds artifacts to future or self SHAs
- allows path names to substitute for typed identities
- trusts caller-supplied accounting over durable evidence
- lacks a precise final human gate

## References

- Generic prompt skeleton: `references/GRAPH-PROMPT-TEMPLATE.md`
- Claim protocol: `references/CLAIM-PROTOCOL.md`
- Review packet format: `references/REVIEW-PACKET.md`
- Adoption guide: `references/ADOPTION-GUIDE.md`
- Fictional worked example: `references/WORKED-EXAMPLE.md`
- JSON schemas: `assets/`
- Validator: `scripts/validate_graph_state.py`
