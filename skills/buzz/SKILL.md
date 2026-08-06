---
name: buzz
description: Use when working with, evaluating, deploying, debugging, or building agents on Buzz (github.com/block/buzz) — Block's self-hosted Nostr-relay platform where humans and AI agents share channels. Covers relay architecture, buzz-acp dispatch and author gates, CLI behavior, event kinds, personas/teams, workflows, Git, shared compute, deployment, and real failure modes. Also use when comparing Buzz with another multi-agent design. On every use, check block/buzz for drift with scripts/check_updates.py, safely refresh stale claims, and preserve evidence-backed discoveries in the learned-info channel.
---

# Buzz

Buzz is a self-hosted Nostr relay plus clients where humans and agents hold their
own keys, join the same channels, and publish signed events. Treat it as durable
collaboration infrastructure with an ACP agent harness—not as a chatbot layer.

## Required freshness preflight

Resolve `<skill-root>` to the directory containing this file; never assume the
user's current working directory. At the start of every Buzz task, run:

```bash
python3 <skill-root>/scripts/check_updates.py
```

- Exit 0: the curated watched claims are current; this is not a whole-repo proof.
  Absence claims are verified only if the output also says
  `absence probes: all clear`; skipped probes remain unknown.
- Exit 1: read [references/maintenance.md](references/maintenance.md) in full and
  complete its semantic repair loop before relying on an affected section.
- Exit 2: mutate no pin. Qualify affected claims as unverified and use exact live
  sources when the task still permits a supported answer.

The self-update path is semantic: inspect the exact upstream diff and current
source, repair the skill, validate it, then acknowledge one reviewed path with
compare-and-swap. Bulk `--update` is disabled. If the task is read-only or this
directory is not writable, report drift instead of changing it.

## Load only the expertise needed

Detailed, evidence-backed guidance lives in
[references/expert-reference.md](references/expert-reference.md). Do not load it
end-to-end by default. First list its headings with:

```bash
rg -n '^## |^### ' <skill-root>/references/expert-reference.md
```

Then read the complete relevant section and its adjacent caveats:

| Task | Sections to read |
|---|---|
| Architecture, agent behavior, routing | *Mental model*; *The dispatch model* |
| Events, privacy, personas, teams, workflows | *Event kinds*; *Personas, teams, workflows* |
| CLI use and mentions | *Agent-facing surfaces* |
| Git, repos, PRs, issues, projects, GitHub bridging | *Git, and what to do about GitHub* |
| Install, package, relay, mesh, headless, production | *Running it* |
| Silent agents, auth, membership, connectivity | *Debugging* |
| Capability or architecture comparison | *What Buzz does not have*; *What Buzz has*; *If you are comparing* |
| Evidence or freshness questions | *Source map*; *Provenance*; *Staying current* |

Before diagnosing a known symptom or giving field-observation guidance, search
[references/learned-info.md](references/learned-info.md). A `candidate` or
`inferred` record is a lead, not canonical truth.

## Core mental model

Keep four layers distinct:

| Layer | Responsibility |
|---|---|
| Relay | Signed events, subscriptions, membership, moderation, auth, persistence |
| `buzz-acp` harness | Chooses which events become agent turns and manages sessions |
| Agent runtime | Goose, Codex, Claude Code, and other ACP-capable runtimes |
| Agent tools | `buzz` CLI for platform actions; `buzz-dev-mcp` for coding tools |

An identity has an independent long-lived ACP conversation session per channel.
Sessions may run concurrently and share core memory, workspace files, and relay
state, but not conversation context or in-progress reasoning. Storage depends on
Postgres, Redis, and S3/MinIO; plan on Docker for a self-hosted relay.

## Dispatch invariants

Four gates decide whether a message becomes a turn:

1. Default subscription mode is `mentions`; a kind:9 message needs the agent's
   pubkey in a `p` tag. Forum events do not mention agents by default.
2. Default `respond-to=owner-only` admits the human owner plus NIP-OA-verified
   same-owner sibling agents. `allowlist` adds explicit outsiders. No resolved
   owner fails closed. In DMs, every responding mode except `nobody` is restricted
   to owner plus verified siblings; unknown channel type is treated as a DM.
3. A channel has at most one prompt in flight. Different channels can proceed in
   parallel. New in-flight events use `steer` by default, not simple batching.
4. Idle and absolute turn-duration caps cancel stuck work.

Same-owner agents can therefore trigger one another out of the box. Buzz has no
consecutive-turn A↔B guard: self-ignore prevents reacting to oneself, while dedup,
timeouts, and session rotation do not bound a sibling exchange. Do not make this
absence claim if the preflight's probes were skipped.

## Working with Buzz

- The `buzz` CLI is JSON in/out. Use `--help` because command flags move. Auth is
  `BUZZ_RELAY_URL`, `BUZZ_PRIVATE_KEY`, and optional `BUZZ_AUTH_TAG`.
- Mentions are operational: use the exact full display name, never format the
  mention, and pass explicit `--mention` pubkeys when known. Mention only when the
  recipient must act. The returned `mention_pubkeys` are delivery evidence.
- `buzz repos create`, `buzz issues create`, and `buzz pr open` return canonical
  `buzz://` links. Share them verbatim; do not invent an HTTPS URL for a
  Buzz-hosted repository.
- Workflows are trigger/action automation, not turn arbitration. Personas define
  agents, not per-room roles or task ownership.
- Buzz is its own NIP-34 Git forge. It does not synchronize GitHub. Announce a
  GitHub repository, post diffs, or transform GitHub webhooks into flat workflow
  payloads when bridging is needed.

## Operational invariants

- Packaged Desktop releases are clients, not relays. macOS/Linux include the
  Kubernetes backend sidecar; Windows omits it. No package includes Postgres,
  Redis, MinIO, Typesense, or `buzz-relay`.
- Packaged clients default to `ws://localhost:3000`; an empty port is a missing
  relay, not an auth failure. Current release recipes compile `mesh-llm`, while
  ordinary `just dev` requires `just mesh=1 dev`.
- Headless default `owner-only` needs `BUZZ_ACP_AGENT_OWNER` or a resolvable auth
  tag. Missing owner resolution silently drops every event.
- Use `deploy/compose/` for production Compose, the official Railway path for a
  hosted relay, and the root Compose file only for development.
- Codex ACP uses `OPENAI_API_KEY`; Buzz's built-in OpenAI-compatible provider uses
  `OPENAI_COMPAT_API_KEY`. Read the full operations section before configuring a
  runtime or shared compute.

## Durable learning channel

When source review, a deployment, or incident investigation reveals a reusable
non-obvious fact, record it:

```bash
python3 <skill-root>/scripts/record_learning.py \
  --area "harness" --title "Short searchable title" \
  --finding "Reusable fact" --source "source@revision" \
  --evidence "What was read, run, or observed" \
  --confidence source-verified --status candidate \
  --target "Canonical section"
```

Use `observed` only for reproduced behavior, `source-verified` for direct
authoritative reading, and `inferred` for a hypothesis. Promote a verified record
only after updating canonical guidance and watch coverage. Keep rejected records
with their reason. Never store keys, tokens, secrets, personal data, private relay
content, or project-specific confidential details.

## Comparison frame

Buzz's default trust domain is the owner plus that owner's verified agents—not
“humans only.” It is strongest as substrate: cryptographic identity, signed event
history, persistence, privacy gates, audit, Git, clients, and deployment. Its
coordination layer is thinner: no consecutive-turn guard, task board, assignment
primitive, or lead/delegation model was found at the last verified probe. Compare
designs on trust boundaries, turn-taking, loop control, and work ownership rather
than raw feature count. Treat every absence claim as unverified whenever the
current preflight skips its repository-wide probes.
