# Graph Engineering Skill

A reusable, tool-agnostic Agent Skill for turning long linear AI workflows into explicit dependency graphs.

It is based on the graph-engineering pattern described by **@0xWast3** in the July 2026 article, *Graph Engineering: How to Run 1,000 AI Agents in Parallel with a Single Prompt*.

## What it does

The skill makes an agent:

1. decompose complex work into bounded nodes,
2. apply the **real-edge test** to every dependency,
3. run independent work in parallel when supported,
4. detect hidden edges caused by shared writes, rate limits, schema changes, exclusive resources, or irreversible actions,
5. use layered fan-in to avoid context collapse,
6. count expected vs. received node results so failed workers cannot disappear,
7. keep orchestration separate from worker execution,
8. retry failed nodes locally rather than restarting successful work.

The core question is:

> Does the downstream task actually require the upstream task's output?

If not, the edge is probably fake.

## Install

Copy the `graph-engineering/` directory into any system that supports the Agent Skills `SKILL.md` format.

The package is intentionally tool-agnostic. It does not require Claude Dynamic Workflows, LangGraph, OpenAI-specific APIs, or a particular multi-agent runtime.

## Suggested triggers

The skill is useful for requests such as:

- "Audit every route in this repository."
- "Research these 40 companies and synthesize the results."
- "Migrate all endpoints to the new interface."
- "Review every module for the same class of bug."
- "Analyze this large batch of documents."
- "Turn this 15-step plan into the fastest safe execution plan."
- "Parallelize this workflow without losing fidelity."

## Package

```text
graph-engineering/
├── SKILL.md
├── README.md
├── examples/
│   └── repository-audit.md
└── references/
    └── provenance.md
```

## Design principles

The skill stays deliberately small. It does not implement a workflow engine. Instead, it teaches any capable agent how to discover and execute the correct dependency graph using whatever concurrency and delegation capabilities exist in the current environment.

If the runtime has no parallel execution, the skill still provides value through dependency clarity, isolated context, local retries, explicit completeness checks, and cleaner synthesis boundaries.

## Attribution and source

Primary inspiration:

- @0xWast3, July 2026, *Graph Engineering: How to Run 1,000 AI Agents in Parallel with a Single Prompt*.

The original X page may require authentication. A public mirror/translation of the article was used to verify the article's node/edge test, parallel fan-out, layered fan-in, hidden-resource edge warning, silent-node-failure check, and orchestrator role.

This repository implementation is original and does not reproduce the article's code or prose verbatim.

## License

No license is included in this generated bundle. Add the license you want for your GitHub skills repository before publishing.
