# Example: Repository Route Audit

## Request

> Audit every route file for missing authentication, unsafe input handling, missing rate limiting, and stack-trace leakage. Produce one consolidated report.

## Bad linear plan

```text
audit route 1
-> audit route 2
-> audit route 3
-> ...
-> audit route 40
-> summarize
```

The route audits do not consume one another's outputs, so the edges between them are false.

## Graph plan

```yaml
graph:
  objective: Audit every route and produce one verified consolidated report.

  nodes:
    - id: discover-routes
      objective: Enumerate route files in scope.
      inputs: [repository]
      output: route-file list
      depends_on: []
      resources: [repository-read]
      completion_check: route list exists and is deduplicated

    - id: audit-route-N
      objective: Audit one route file against the four checks.
      inputs: [one route file, audit rubric]
      output: structured findings for one file
      depends_on: [discover-routes]
      resources: [repository-read]
      completion_check: all four checks have explicit results

    - id: consolidate-batch-N
      objective: Consolidate a bounded group of route findings.
      inputs: [validated route findings]
      output: batch findings
      depends_on: [corresponding audit-route nodes]
      resources: []
      completion_check: received count equals expected count

    - id: final-report
      objective: Merge batch findings into one severity-ranked report.
      inputs: [all batch findings]
      output: final report
      depends_on: [all consolidate-batch nodes]
      resources: []
      completion_check: every discovered route is represented

  edges:
    - from: discover-routes
      to: audit-route-N
      reason: audit workers need the discovered file identities
    - from: audit-route-N
      to: consolidate-batch-N
      reason: batch consolidation consumes route audit results
    - from: consolidate-batch-N
      to: final-report
      reason: final report consumes batch results

  parallel_layers:
    - [discover-routes]
    - [all audit-route nodes]
    - [all consolidate-batch nodes]
    - [final-report]

  fan_in:
    strategy: layered
    expected_results: 40
    batch_size: 30

  critical_path:
    - discover-routes
    - audit-route-N
    - consolidate-batch-N
    - final-report

  hidden_edge_check:
    shared_writes: none; audit nodes are read-only
    rate_limits: honor runtime/tool concurrency limits
    schema_changes: none
    exclusive_resources: none
    irreversible_actions: none
```

## Completeness gate

Before final synthesis:

```text
expected route audits = number of discovered route files
received valid audits = count of validated route audit outputs

if expected != received:
    identify missing nodes
    retry or mark incomplete
    do not silently claim full coverage
```

This preserves the speed benefit of fan-out without sacrificing coverage.
