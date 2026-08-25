---
name: graph-engineering
description: >
  Turn complex multi-step work into an explicit dependency graph so independent
  tasks can run in parallel, real dependencies stay ordered, large fan-ins do not
  collapse context, hidden shared-resource conflicts are surfaced, and missing
  node results cannot silently disappear. Use for large coding, research, audit,
  migration, analysis, or batch workflows that would otherwise be written as a
  long "do A, then B, then C" chain.
---

# Graph Engineering

Design the shape of the work before executing the work.

The core rule is simple:

> Add an edge only when the downstream node actually requires something produced
> by the upstream node, or when a shared-resource constraint makes ordering necessary.

Do not treat chronology, narration, or the phrase "and then" as a dependency.

## When to use this skill

Use this skill when one or more of these are true:

- The task has many subtasks, files, sources, records, endpoints, modules, or targets.
- A proposed plan has more than roughly four sequential steps.
- Several subtasks appear to use the same starting inputs and may be independent.
- The task would benefit from multiple workers, agents, tool calls, or workstreams.
- A previous attempt was slow because everything ran serially.
- A previous attempt lost detail as context accumulated.
- A final synthesis must incorporate many independent results.
- Missing one worker result would make the final answer incomplete or misleading.

Do not force a graph onto a genuinely short linear task.

## Mental model

A **node** is one bounded unit of work:

- one objective,
- defined inputs,
- defined output,
- clear completion condition.

An **edge** is a real dependency.

For every proposed edge `A -> B`, ask:

> Does B literally need A's output in order to perform B correctly?

If yes, keep the edge.

If no, remove it and consider running A and B in parallel.

### Hidden edges

Data flow is not the only reason two nodes may need ordering. Before declaring
nodes independent, check whether they share a constrained resource:

- both write the same file or mutable artifact,
- both mutate the same repository region,
- both consume an exclusive device or environment,
- both depend on a schema/interface that one of them changes,
- both contend for a rate-limited API or quota,
- one performs an irreversible or externally visible action that requires prior verification.

If a shared resource creates a conflict, represent that constraint explicitly.
Do not pretend the nodes are independent merely because their prompts are unrelated.

## Workflow

### 1. Decompose the request into nodes

Break the task into the smallest useful units that can succeed or fail independently.

Each node should have:

- `id`
- `objective`
- `inputs`
- `output`
- `depends_on`
- `resources`
- `completion_check`

If a node description contains two unrelated jobs, split it.

Do not execute yet.

### 2. Run the real-edge audit

For every proposed dependency, write the reason.

Acceptable reasons include:

- downstream consumes upstream output,
- upstream changes a schema/interface downstream needs,
- shared mutable resource requires serialization,
- approval or verification must precede a consequential action.

Reject an edge whose only justification is:

- "it comes next,"
- "the prompt said then,"
- "it feels cleaner in this order,"
- "these tasks are related."

When two nodes use the same original inputs but do not consume each other's outputs,
they normally belong in the same parallel layer.

### 3. Build the graph

Represent the plan as a directed graph.

Prefer this broad production shape when applicable:

```text
                         Orchestrator
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
          Node 1           Node 2           Node N
             |                |                |
             +----------------+----------------+
                              |
                     Layered consolidation
                              |
                         Final synthesis
```

The orchestrator plans and routes work. It should not perform the substantive
worker jobs itself unless the environment has no delegation mechanism.

### 4. Identify the critical path

Find the longest chain of real dependencies.

That chain is the latency floor.

Do not add more workers to a path that cannot be parallelized. To shorten wall-clock
time, first look for false edges that can be removed or large nodes that can be
safely split.

### 5. Execute ready nodes in parallel

A node is ready when all real dependencies have completed successfully.

Run all ready independent nodes concurrently when the environment supports it.

If parallel execution is unavailable, preserve the graph anyway and execute nodes
serially while maintaining their independence. The graph is still useful for
context isolation, retries, validation, and future execution.

Pass each worker only the inputs it needs.

Do not make every worker inherit the full accumulated conversation unless necessary.

### 6. Validate every node result

Before fan-in, record for each expected node:

- node id,
- status,
- output location or content,
- validation status,
- error if any.

Never infer success merely because no error was surfaced.

A failed or missing node must remain visible.

### 7. Prevent silent node loss

Every consolidation node must know how many inputs it expects.

Before synthesis:

```text
expected = number of required predecessor nodes
received = number of valid predecessor results
```

If `received != expected`, do not silently produce a complete-looking result.

Instead:

1. identify missing/failed nodes,
2. retry them if retries are appropriate,
3. otherwise mark the final output explicitly incomplete.

For critical workflows, fail closed rather than synthesize partial results.

### 8. Use layered fan-in when the graph is wide

Do not send hundreds or thousands of raw worker outputs into one final context.

When fan-in is large, consolidate hierarchically:

```text
Workers 1..30    -> Batch summary A
Workers 31..60   -> Batch summary B
Workers 61..90   -> Batch summary C
...
Batch summaries  -> Final synthesis
```

Choose batch size based on result size and context limits. A range of roughly
20 to 50 workers per batch is a useful starting point, not a hard rule.

Batch reducers must preserve facts needed downstream. Prefer structured reduction
over lossy prose when possible.

### 9. Keep synthesis separate from collection

The final synthesis node should consume completed, validated upstream outputs.

Its job is to:

- reconcile findings,
- detect conflicts,
- group or rank results,
- preserve uncertainty,
- produce the requested final artifact.

It should not quietly redo missing worker tasks.

### 10. Verify before consequential actions

For deploys, sends, deletes, writes to production, merges, purchases, permission
changes, or other difficult-to-reverse actions, add a verification or human-approval
node before the action.

Example:

```text
Generate change -> Independent verify -> Approval gate -> Execute change
```

Parallelism does not override safety or authority boundaries.

## Required planning output

Before substantial execution, produce a compact graph plan in this form:

```yaml
graph:
  objective: <overall goal>

  nodes:
    - id: <node_id>
      objective: <one bounded job>
      inputs: [<inputs>]
      output: <defined result>
      depends_on: [<real predecessor ids>]
      resources: [<shared/exclusive resources, if any>]
      completion_check: <how success is known>

  edges:
    - from: <node_a>
      to: <node_b>
      reason: <why this is a real dependency>

  parallel_layers:
    - [<nodes that may run together>]
    - [<next ready nodes>]

  fan_in:
    strategy: direct | layered
    expected_results: <count>
    batch_size: <number or null>

  critical_path:
    - <node ids>

  hidden_edge_check:
    shared_writes: <none or details>
    rate_limits: <none or details>
    schema_changes: <none or details>
    exclusive_resources: <none or details>
    irreversible_actions: <none or details>
```

The representation may be adapted to the user's requested format, but the same
information must remain explicit.

## Execution ledger

For nontrivial runs, maintain a compact ledger:

| Node | Status | Depends on | Output | Validation |
|---|---|---|---|---|
| node-a | complete | none | ... | pass |
| node-b | running | node-a | ... | pending |
| node-c | failed | none | ... | fail |

Allowed statuses:

- `pending`
- `ready`
- `running`
- `complete`
- `failed`
- `blocked`
- `skipped`

Do not mark a node `complete` until its completion check passes.

## Failure and retry rules

Retry locally whenever possible.

If one independent node fails:

- do not rerun successful siblings,
- retry only the failed node,
- preserve accepted outputs,
- rerun downstream nodes only if they depend on the changed result.

If an upstream result changes, identify and invalidate only its descendants.

If the graph itself is wrong, revise the graph explicitly rather than hiding the
change inside a worker prompt.

## Scaling rules

Scale width only after the graph is correct at smaller size.

Start with a modest concurrency cap. Increase it after observing:

- tool/API rate limits,
- context size,
- token/cost behavior,
- write conflicts,
- failure rate,
- consolidation quality.

Do not equate "more agents" with "better graph."

A small accurate graph is better than a large graph with false independence.

## Anti-patterns

Avoid:

- **Narrative chains:** serializing independent work because it was listed in order.
- **God nodes:** one worker researches, edits, tests, reviews, and summarizes everything.
- **Shared-context dependency:** workers rely on unstated conversational history.
- **Unbounded fan-in:** one synthesizer receives every raw result regardless of size.
- **Silent partial success:** final output looks complete despite missing workers.
- **Parallel shared writes:** independent agents overwrite the same mutable artifact.
- **Reviewer theater:** a verifier exists but cannot block or change promotion.
- **Orchestrator implementation:** the planner becomes another giant worker.
- **Fleet-first scaling:** hundreds of workers before correctness is demonstrated.
- **Global retries:** one failure restarts work that already succeeded.

## Quality gate

Before finalizing, confirm:

- Every edge has a concrete dependency reason.
- No obvious false edge remains.
- Hidden shared-resource edges were checked.
- Every node has one bounded job and defined output.
- All expected nodes are accounted for.
- Failed or missing nodes are explicit.
- Large fan-in is layered or otherwise context-safe.
- The final synthesis consumes validated results.
- Irreversible actions are gated.
- Only affected descendants are rerun after changes.
- The graph is no wider or more complex than the task requires.

## Attribution

This skill operationalizes the graph-engineering pattern described by
@0xWast3 in the July 2026 article commonly titled
"Graph Engineering: How to Run 1,000 AI Agents in Parallel with a Single Prompt."

The skill preserves the article's central ideas:

- loops versus graphs,
- nodes and real dependency edges,
- the "does the next step read the previous output?" test,
- parallel fan-out,
- layered fan-in,
- hidden shared-resource edges,
- expected-result counting to catch silent node failures,
- an orchestrator that decomposes and routes rather than doing all worker work.

The wording and implementation of this skill are original and tool-agnostic.
