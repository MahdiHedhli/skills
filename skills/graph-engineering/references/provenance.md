# Provenance

## Primary source

The conceptual source for this skill is the July 2026 article by **@0xWast3** commonly titled:

**Graph Engineering: How to Run 1,000 AI Agents in Parallel with a Single Prompt**

Original X status/article reference:

`https://x.com/0xwast3/status/2079899723947712845`

## Concepts intentionally preserved

The skill implements the article's conceptual graph:

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
                 Layered fan-in
                        |
                  Final synthesis
```

It also preserves these operational rules:

1. A node is a unit of work.
2. An edge exists when a downstream node needs an upstream output.
3. "Then" does not automatically imply an edge.
4. Independent nodes should fan out.
5. Large result sets should use layered consolidation rather than one massive fan-in.
6. Shared mutable resources and constrained APIs create hidden dependencies.
7. Consolidation must compare expected and received node counts.
8. The orchestrator decomposes and routes; it should not become the primary worker.

## Adaptations in this skill

The reusable skill adds tool-agnostic operational guardrails that make the article's graph pattern safer to apply across coding, research, and operational work:

- explicit node contracts,
- execution ledger,
- local retry/invalidation rules,
- critical-path identification,
- consequential-action verification gates,
- guidance for runtimes without parallel execution.

These are adaptations, not claims about the source article.

## Publication note

Before publishing this bundle, choose a repository license and add it at the repository root or within this directory, depending on your skills-repo structure.
