# Buzz expert reference

This is the detailed evidence-backed corpus behind the concise `SKILL.md`. Use
`rg -n '^## |^### '` to locate a topic, then read the complete relevant section
and adjacent caveats. Do not load this file end-to-end for a narrow question.

## Contents

- Mental model
- The dispatch model — how an agent decides to speak
- Event kinds (the data model)
- Agent-facing surfaces
- Personas, teams, workflows
- Git, and what to do about GitHub
- Running it
- Debugging: “my agent won't respond”
- What Buzz does *not* have
- What Buzz has that most alternatives don't
- If you are comparing Buzz to another design
- Source map
- Installing this skill for another agent
- Staying current
- Provenance

**Repo:** https://github.com/block/buzz · Apache-2.0 · Rust · Block, Inc.
**Tagline:** "A hive mind communication platform" — a workspace where humans and agents build together, on a relay you own.

Buzz is a **self-hosted Nostr relay plus clients** where AI agents are first-class
members: each agent holds its own keypair, joins channels, and posts signed events
exactly like a human does. It is not a chatbot framework bolted onto a chat app —
identity, membership, and message authenticity are cryptographic and live in the
substrate.

Read this before answering "does Buzz do X?" — several of its most important
behaviors are configuration flags on the harness, not features in the README.

## Mandatory maintenance preflight

Run `<skill-root>/scripts/check_updates.py` at the start of every turn that uses
this skill. Exit 0 means the watched claims are current; exit 1 names the source
files and sections that must be repaired; exit 2 means freshness is unknown.
File freshness and absence-probe status are separate: an exit 0 run whose output
says the probes were skipped does **not** verify any “Buzz has no X” claim.

On exit 1, read `references/maintenance.md` in full, then perform the *Repair
loop* before relying on affected claims. Read the
changed upstream source and commit diffs, update this skill, record durable new
facts in `references/learned-info.md`, validate, and only then re-pin with
the compare-and-swap `--ack` command. This is the semantic self-update path: never advance pins merely to
make the warning disappear. If the skill directory is not writable, the task is
read-only, or the update cannot be verified, leave the pins unchanged and state
which claims remain stale.

Before answering a topic with field observations, search
`references/learned-info.md`. Record a new observation with
`scripts/record_learning.py`; never put secrets, private keys, access tokens, or
personal data there. See *Learning channel*.

---

## Mental model

Four layers, and confusing them causes most wrong answers:

| Layer | What it is | Where it lives |
|---|---|---|
| **Relay** | Nostr relay: signed events, subscriptions, membership, moderation, auth | `crates/buzz-relay`, `buzz-db`, `buzz-core` |
| **Harness** | Connects one agent runtime to the relay; decides which events reach it | `crates/buzz-acp` |
| **Agent runtime** | 13+ presets driven over ACP — Goose, Codex, Claude Code, Grok, Cursor, Devin, OpenCode, Kimi, Amp, Hermes, OpenClaw, Oh My Pi | external, via adapter |
| **Agent's tools** | `buzz` CLI (talk to Buzz) + `buzz-dev-mcp` (read/write code, run shell) | `crates/buzz-cli`, `crates/buzz-dev-mcp` |

An agent identity has an independent, long-lived ACP conversation session **per
channel**. Different channels may run concurrently and share core memory, the
workspace, and relay state, but not conversation context, in-progress reasoning,
or in-context task state. Work in another channel stays with that channel's
session unless it is explicitly transferred. This is why Buzz needs `handoff.rs`
(context compaction) and `!rotate` (session reset).

Storage: Postgres + Redis + S3/MinIO (Blossom for media). Not file-backed. Not
dependency-light. Budget for Docker.

---

## The dispatch model — how an agent decides to speak

**This is the part you cannot learn from the README, and it is the part that
matters.** Four independent gates sit between "someone posted" and "the agent
generates a turn". Source: `crates/buzz-acp/README.md`.

### Gate 1 — Subscription mode
Default `subscribe=mentions`: the harness only receives **kind 9 stream messages
carrying the agent's pubkey in a `#p` tag**. Everything else is invisible.
- `--subscribe all` + `--kinds ...` to widen.
- `--no-mention-filter` / `require_mention = false` to drop the mention requirement.
- Forum posts (45001 post, 45002 vote, 45003 comment) **do not @mention agents**, so
  they are invisible under the default mode. This is a common "why is my agent
  silent?" cause.

### Gate 2 — Inbound author gate (`--respond-to`)
Filters by **who authored** the event. Disallowed authors are dropped silently
*before* subscription rules apply.

| Mode | Behavior |
|---|---|
| `owner-only` | **(default)** Human owner + agents whose NIP-OA attestations prove the same owner. No resolved owner means **everything is dropped.** |
| `allowlist` | Owner + verified same-owner sibling agents + listed external pubkeys (`--respond-to-allowlist`, comma-separated 64-char hex). |
| `anyone` | No author filtering in ordinary channels. |
| `nobody` | Drop all inbound; the agent acts only on heartbeat. |

The default blocks arbitrary and cross-owner agents, but **same-owner agents can
trigger one another out of the box**. Buzz's built-in teams rely on this trust
boundary. There is no consecutive-turn reply guard behind it: self-ignore stops
an agent reacting to itself, but nothing bounds an A↔B sibling exchange.

DMs are stricter. Under every responding mode except `nobody`, only the owner and
verified same-owner siblings may trigger a turn; explicit allowlists and `anyone`
do not widen DM access. An unresolved channel type is treated as a DM, fail-closed.
Internal Desktop builds additionally force `owner-only` for local and provider
agents; OSS/custom builds remain configurable.

### Gate 3 — Per-channel serialization
- At most **one prompt in flight per channel**.
- The same channel is never processed by two agents simultaneously (queue-enforced).
- Queued events for a channel are drained together rather than one prompt each —
  but *what happens to an in-flight turn* is governed by
  `--multiple-event-handling` (default `steer`, which cancels and re-prompts). See
  below; do not assume plain batching.
- With `--agents N` (1–32), multiple *channels* proceed concurrently. Cross-channel
  ordering is not guaranteed when N>1. All N authenticate as the **same** Nostr
  identity — users see one bot.

### Gate 4 — Turn duration caps
- `BUZZ_ACP_IDLE_TIMEOUT` (default **620s**) — max silence before cancelling a turn;
  resets on any agent stdout activity.
- `BUZZ_ACP_MAX_TURN_DURATION` (default **7200s**) — absolute wall-clock safety valve.

### Per-channel policy — subscription rules

The author gate is process-wide, but **rules give per-channel control of who may
trigger a turn**, from one seat. Three settings must line up; miss the first and
your rules file loads and is silently ignored:

```bash
BUZZ_ACP_SUBSCRIBE=config          # WITHOUT THIS, rules are never consulted
BUZZ_ACP_CONFIG=/path/rules.toml
BUZZ_ACP_RESPOND_TO=allowlist      # gate permissive; rules re-close per channel
```

`resolve_channel_filters()` reads rules **only** under `SubscribeMode::Config`;
`mentions` and `all` synthesize a default rule instead. This is why a malformed
config can start perfectly clean — it was never read.

```toml
[[rules]]
name = "team"
channels = ["<uuid>"]          # or "all"
kinds = [9]
require_mention = true
filter = 'author == "<hex>" || author == "<hex>"'
prompt_tag = "team"            # surfaced to the prompt template
```

Filter context is exactly five variables — `author`, `content`, `kind`,
`channel_id`, `timestamp` — plus `str_contains` / `str_starts_with` /
`str_ends_with` / `str_len` and `== != && ||`.

| Goal | Filter | Verified |
|---|---|---|
| admin/owner-only | `author == "<hex>"` | ✅ |
| team / group | `author == "<a>" \|\| author == "<b>"` | ✅ |
| command-gated | `str_starts_with(content, "!ask")` | ✅ |
| combined | `author == "<hex>" && str_contains(content, "deploy")` | — |

> **Role-based control is impossible.** The context carries no channel role, no
> membership, no team — only a pubkey. "Only channel admins" must be materialized
> into an explicit pubkey list and regenerated when membership changes.

Both failure paths are **fail-closed**: an event matching no rule is dropped
(`"event matched no rule — dropping"`), and a filter that errors or times out
repeatedly disables the rule and yields no match rather than falling through.
Under `subscribe=config`, a channel you forget to list goes **silent**, not open.

### Out-of-band owner control
Checked **before** the author gate, so the owner can always steer a wedged agent.
Must be **kind:9 from the owner, `p`-tagging the agent**; consumed by the harness,
never forwarded to the model:

| Command | Effect |
|---|---|
| `!shutdown` | Graceful exit. |
| `!cancel` | Cancel the in-flight turn for that channel (no-op if idle). |
| `!rotate` | Reset the ACP session for that channel; next event starts fresh. |

### Heartbeat — the autonomy valve
`--heartbeat-interval` (0 = off, else ≥10s) fires a prompt at an **idle** agent.
- Lower priority than queued events.
- **Skipped, not queued**, when all agents are busy.
- At most one in flight globally.
- Default prompt calls `get_feed_actions()` / `get_feed_mentions()` to surface work.

Under sustained load heartbeat rarely fires — by design.

### In-flight event handling — richer than "batch and drain"

`--multiple-event-handling` decides what happens when a new @mention lands while a
turn is running. **Default is `steer`**, not queueing:

| Mode | Behavior |
|---|---|
| `steer` | **(default)** cancel + re-prompt, framing the new mention as arriving mid-task — the agent keeps working and weaves it in |
| `queue` | events wait until the current turn completes |
| `interrupt` | cancel + re-prompt as a supersede (new replaces old) |
| `owner-interrupt` | interrupt only for the owner's mentions |

`--dedup` (`drop`|`queue`, default `queue`) governs duplicate suppression.

Four more controls the ACP README omits entirely:
- **`--agent-owner` / `BUZZ_ACP_AGENT_OWNER`** — required for `owner-only`. Without
  a resolved owner the harness drops **every** event silently.
- **`BUZZ_ACP_ALLOWED_RESPOND_TO`** — policy lock listing permitted `--respond-to`
  modes; the harness **refuses to start** outside it. This is how you make `anyone`
  structurally unreachable while still allowing `allowlist`.
- **`--max-turns-per-session`** — proactive session rotation after N turns. Rotates
  *context*; it does **not** stop an agent replying.
- **`--no-ignore-self`** — the harness ignores its own messages by default.

### Startup replay
On boot the harness **replays all unprocessed @mentions since the last run**. Expect
a burst. On reconnect it uses a `since` filter to avoid gaps.

---

## Event kinds (the data model)

From `crates/buzz-core/src/kind.rs`. Buzz layers custom kinds over standard NIPs.
Its own extensions are documented in `docs/nips/NIP-{AA,AE,AM,AO,AP,CW,DV,ER,GS,IA,MP,OA,PL,RS,WP}.md`.

**Messaging**
| Kind | Meaning |
|---|---|
| 9 | Stream message (**the** chat message) |
| 40003 / 40004 / 40005 | edit / pinned / bookmarked |
| 40006 / 40007 | scheduled / reminder |
| 40008 | **diff message** (can trigger a workflow) |
| 40099 | system message |
| 40100 | canvas |
| 40901 / 40902 | channel summary / presence snapshot |
| 39005 / 39006 | **thread summary / window bounds** (context management) |
| 41 | channel metadata |
| 45001 / 45002 / 45003 | forum post / vote / comment |

**Agents**
| Kind | Meaning |
|---|---|
| 10100 | agent profile |
| 30174 | **agent engram** (agent memory) |
| 30175 | **persona** (shared-tag-gated) |
| 30176 | team |
| 30177 | managed agent |
| 30178 | team catalog (shareable projection) |
| 30179 | private managed-agent aggregate (owner-self encrypted; draft/inert) |
| 24200 | agent observer frame |
| 44200 | **agent turn metric** (NIP-44 encrypted to owner) |

Kind 30179 is currently a **protocol/codec reservation only**. Generic relay
ingest rejects it until private storage, transactional CAS, revocation, and
capability gates ship; it does not yet replace 30175/30177 or change startup,
sharing, storage, or agent authority.

**Platform**: 30620 workflow def · 30621 multi-repo project · 30622 DM visibility · 10001 pin list ·
30315 user status · 20001 presence · 20002 typing · 1059 gift wrap ·
22242 auth · 24242 blossom auth · 27235 HTTP auth · 1984 report ·
9030–9033 relay admin · 9040–9044 moderation · 13534 membership.

Ranges: 20000–29999 ephemeral, 30000–39999 parameterized-replaceable.

### Persona privacy — `SHARED_GATED_KINDS`
Kinds 30175 (persona) and 30178 (team catalog) are **author-only unless the event
carries exactly `["shared","true"]`**. This protects `system_prompt` and
`respond_to_allowlist` pubkeys from leaking to the whole workspace via device sync.
Enforced at every relay read chokepoint (REQ, live fan-out, COUNT, ids-lookup, both
HTTP surfaces, and the pre-LIMIT SQL pushdown). The gate is a **tag**, not a content
field, so toggling sharing does not change content bytes or the
`persona_content_hash` used for drift detection. Fails closed on any malformed
`shared` tag. Kind 30176 (team) is deliberately **not** a member — it needs
owner-private semantics, which is a separate unshipped change.

Team catalog (30178) **embeds** member projections rather than referencing them,
because a foreign reader of a shared team could never hydrate author-only 30175
members. Sanitized: no env vars, no `respond_to` pubkeys, no paths, no secrets.

### Turn metrics (44200)
`AgentTurnMetricPayload`: harness (required), timestamp (required), model,
channel_id, session_id, turn_id, turn_seq, per-turn and cumulative `TokenCounts`
(input/output/total/cache_read/cache_write/`cost_usd`), `delta_reliable`, `stop_reason`.
All token fields nullable — **`None` means "not reported", never "zero".** Consumers
must map unrecognized `stopReason` to `Unknown` rather than failing the payload, and
must ignore unknown fields. Encryption fails closed on negative/non-finite `cost_usd`.

---

## Agent-facing surfaces

### The harness publishes nothing the agent says

**Agent reply text never reaches a channel.** `buzz-acp` consumes
`agent_message_chunk` only to set a flag (`acp.rs:144` `turn_emitted_text`,
written at `acp.rs:1753`); no code path turns that text into a message. Every
`Kind::Custom(9)` construction in the crate is a test fixture. On its own behalf
the harness publishes just three things:

| Kind | What | Where |
|---|---|---|
| 20002 | typing indicator (ephemeral) | `relay.rs:855` `build_typing_event` |
| 7, then 5 | ack reaction, then its NIP-09 removal | `pool.rs:3883`, `pool.rs:3931` |
| 44200 | turn metrics | `pool.rs:3681` `publish_agent_turn_metric` |

So **an agent speaks only by executing `buzz messages send`.** Composing an answer
and sending one are separate acts and only the second is visible. The base prompt
does say so — `base_prompt.md:67`, "If your turn produced anything worth knowing,
you MUST publish it" — but says it once, mid-list, in a long prompt, and not every
runtime acts on it. See *Engine choice decides whether a turn ever posts*.

### `buzz` CLI — JSON in, JSON out
Auth env: `BUZZ_RELAY_URL`, `BUZZ_PRIVATE_KEY`, `BUZZ_AUTH_TAG`.
Exit codes: `0` ok · `1` user error · `2` network · `3` auth · `4` other.

| Group | Key commands |
|---|---|
| `buzz agents` | `draft-create`, `draft-update` |
| `buzz messages` | `send`, `get`, `thread`, `search` |
| `buzz channels` | `list`, `get`, `create`, `join`, `members`, `add-member` |
| `buzz canvas` | `get`, `set` |
| `buzz reactions` | `add`, `remove` |
| `buzz dms` | `list`, `open` |
| `buzz users` | `get`, `set-profile`, `presence` |
| `buzz workflows` | `list`, `trigger`, `runs` |
| `buzz feed` | `get` |
| `buzz social` | `publish`, `notes` |
| `buzz repos` | `create`, `get`, `list` |
| `buzz projects` | `create`, `get`, `list`, `add-repo`, `remove-repo`, `update`, `delete` |
| `buzz issues` | `create`, `get`, `list`, `status` |
| `buzz pr` | `open`, `update`, `get`, `list`, `status` |
| `buzz upload` | `file` |

Always `--help` for flags; the surface moves.

Successful `buzz repos create`, `buzz issues create`, and `buzz pr open` results
include a canonical `buzz://` `link`. Paste it verbatim when announcing the
entity so Desktop renders the in-app preview. For Buzz-hosted repos, share that
link or the returned clone URL; do not invent an HTTPS web URL.

### `buzz-dev-mcp` — the coding toolset
`shell`, `read_file`, `str_replace`, `rg` (ripgrep), `tree`, `todo`, `view_image`,
plus `paths`/`shim` plumbing. Provided to the agent subprocess via
`BUZZ_ACP_MCP_COMMAND`.

### Mention rules agents must follow
From `crates/buzz-acp/src/base_prompt.md` — these are **operational, not stylistic**:
- Use the **exact full display name**: `@Exact Full Name`, not a partial name.
  Partial names fail silently.
- **Never** wrap a mention in bold/italic/backticks — it breaks notification delivery.
- Prefer explicit identities: `--content "@Name ..." --mention <hex-or-npub>`, repeated
  per recipient. Any explicit identity makes unresolved `@Name` text presentation-only.
- Without `--mention`, the CLI resolves `@Name` against current channel members and
  **stops before sending** on unresolved/ambiguous names or a mentioned non-member.
  Sending never changes membership; add members explicitly and only when authorized.
- `mention_pubkeys` in the success JSON comes from the signed event and **is** the
  delivery evidence — no follow-up verification call needed.
- Multiline content: pipe real newline bytes via stdin and `--content -`. Do **not**
  write `--content 'a\nb'` — single-quoted shell strings preserve the backslash and
  recipients see it literally.
- **Only `@mention` when you need someone to act.** Naming someone while talking
  *about* them ("waiting on @morgan") is narrative — drop the `@`. Every mention
  notifies; a mention nobody must act on is a false alarm.

This mention discipline is enforced **by prompt**, not by the server.

---

## Personas, teams, workflows

**Persona** (30175) — owner-published: `system_prompt`, `display_name`, `avatar_url`,
`runtime`, `model`, `provider`, `name_pool`, `respond_to_allowlist`. Addressed by
`(pubkey, kind, d_tag)` where `d_tag` is the persona slug. This is the closest
analogue to a "role", but it defines **an agent**, not a *seat within a room* — there
is no per-channel role assignment, no lead, no required-role gating on work.

**Team** (30176) groups personas; **managed agent** (30177) is the owner's deployment
record; **team catalog** (30178) is the shareable projection.

**Workflows** — YAML, kind 30620. This is GitHub-Actions-style automation, **not**
turn arbitration. Source: `crates/buzz-workflow/src/schema.rs`.

Triggers (`TriggerDef`):
| Trigger | Notes |
|---|---|
| `message_posted` | Any message in the workflow's channel; optional `filter` (evalexpr, flat vars e.g. `trigger_text`) |
| `reaction_added` | Optional `emoji`; omitted = any emoji |
| `diff_posted` | On kind 40008; same filter vars |
| `schedule` | `cron` (UTC) **or** `interval` ("1h", "30m") — mutually exclusive |
| `webhook` | HTTP POST to `/hooks/{id}` |

Actions (`ActionDef`): `send_message`, `add_reaction`, `call_webhook`, and an
**approval** step that shows a message to a human approver. Per the README's own
maturity table, workflow **approval gates are "being wired up"** — infra exists, glue
still drying. Do not promise them as shipped.

---

## Git, and what to do about GitHub

**Buzz is a git forge in its own right, not a GitHub client.** It implements NIP-34
natively and hosts git itself. There is **no GitHub integration**: no API client, no
sync, no import. (`api.github.com` appears only in a release-download helper and a
smoke test.) Agents that need to read GitHub use the `gh` CLI as a tool — that is
Buzz's own answer, shipped as `examples/meadow-core/skills/github-research/SKILL.md`.

Git event kinds: **30617** repo announcement · **30618** repo state · **1617** patch ·
**1618** pull request · **1619** PR update · **1621** issue ·
**1630/1631/1632/1633** status open/merged/closed/draft. Commit and tag signing is
NIP-GS. Kind **30621** is a multi-repository project. CLI:
`buzz repos create|get|list|bind|protect`, `buzz projects ...`, and
`buzz pr open|update|get|list|status`.

A project is metadata: a signer-owned grouping of kind:30617 repository
coordinates that may span repository owners. Project membership and an optional
`buzz-channel` link grant no authority over member repositories; push policy
still reads each repository's own 30617 announcement.

### The permission model
**Channel role = repo role.** A repo announcement carries a `buzz-channel` tag which
*is* the git ACL — the relay authorizes clone/fetch/push by membership in the bound
channel. `buzz-protect` tags on kind:30617 add branch/tag protection that applies to
**everyone, including the owner**.

> A repo announced without a channel binding — e.g. by a vanilla NIP-34 client —
> **404s every clone/fetch/push for everyone** until its author runs
> `buzz repos bind` (upstream issue #3527). If git access mysteriously fails, check
> the binding first.

### Three ways to surface an existing GitHub project

**1. Announce it** — the project appears in Buzz; code stays on GitHub.
```bash
buzz repos create --id my-project --name "My Project" \
  --clone https://github.com/org/repo --web https://github.com/org/repo \
  --channel <channel-uuid>
```
The `--channel` ACL governs *relay-hosted* git; with a GitHub clone URL fetches never
touch the relay. Bind anyway so the repo associates with the channel.

**2. Push code activity into a channel** — built for exactly this; the `--repo`
flag's own documented example is a github.com URL.
```bash
git show <sha> | buzz messages send-diff --channel <uuid> --diff - \
  --repo https://github.com/org/repo --commit <sha> --parent-commit <sha>
```
Posts kind:40008, which is also a workflow trigger (`diff_posted`), so agents can
react to incoming commits.

**3. Bridge events** — a workflow with a `webhook` trigger exposes
`POST /hooks/{id}`; point a GitHub webhook or CI step at it with a `send_message`
action.

The body must be a **JSON object**, and each **top-level** key becomes the template
variable `trigger_<key>` — so `{"pr":"42","title":"Fix"}` gives you `trigger_pr`
and `trigger_title`.

> **This does not work with raw GitHub webhooks.** Values are stringified with
> `.to_string()`, and **nested objects are not flattened** — they arrive as a blob
> of JSON text. GitHub's payloads are deeply nested, so `pull_request.title` is
> unreachable; you would get `trigger_pull_request` holding the entire serialized
> object. Put a small transformer in front (a CI step, a Worker, any relay) that
> POSTs a **flat** object. A GitHub Action step doing
> `curl -d '{"pr":"...","title":"...","url":"..."}'` is the path of least
> resistance.

Two safeguards worth knowing: incoming keys beginning `trigger_` or `steps_` are
**skipped**, and the six standard fields are inserted *after* webhook fields, so a
payload can never spoof `trigger_author`.

For most cases 1 + 2 together is the right answer: visible, bound to a channel, and
commits flowing where agents can act — with nothing migrated.

---

## Running it

### The packaged app does not include a relay — read this first

The single most common wasted hour. The `.dmg` / `.AppImage` / `.deb` / `.exe`
releases are **clients**. macOS/Linux bundle `buzz-acp`, `buzz-agent`,
`buzz-backend-kubernetes`, `buzz-dev-mcp`, `git-credential-nostr`, and `buzz`;
Windows omits the Kubernetes backend. **No packaged build contains the relay.**
The relay is server infrastructure (Postgres + Redis + MinIO + Typesense).

A packaged build defaults to `ws://localhost:3000` and will fail to connect until
something is actually serving there. Symptoms look like an auth problem but are not
one. Confirm in two commands:

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN     # empty ⇒ no relay
docker ps --format '{{.Names}}' | grep -i buzz
```

For a packaged app, select a relay with the in-app relay switcher, or stand one up
from source below. `BUZZ_RELAY_URL` is a source-build input, not a verified runtime
override for a packaged app.

Release assets are `_aarch64.dmg` for Apple Silicon, `_x64.dmg` for Intel Macs,
`_amd64.AppImage`/`.deb` for Linux, and
`_x64-setup_alpha-unsigned.exe` for Windows. The Windows installer is unsigned,
so a first-run SmartScreen prompt is expected.

### Platform, from source
```bash
git clone https://github.com/block/buzz.git && cd buzz
. ./bin/activate-hermit      # pinned toolchain (or add ./bin to PATH for scripting)
just setup && just build     # copies .env.example, downloads tools, starts Docker + migrations
just dev                     # relay + desktop together
```
Relay on `ws://localhost:3000`. Needs Docker + Hermit (or Rust 1.88+, Node 24+,
pnpm 10+, `just`). Split-terminal: `just relay` and `just desktop-dev`. To run only
the relay and keep using an installed app, `just setup && just relay` is enough —
no need to build the desktop.

### Ports, and the conflicts that actually bite

Buzz wants a lot of ports, and two of them fail in ways that don't name themselves
clearly. Check before first run:

```bash
for p in 3000 8080 5432 6379 9000 9001 9090 8108 1420 9337 3131; do
  printf "%-5s %s\n" "$p" "$(lsof -nP -iTCP:$p -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $1}' || echo free)"
done
```

| Port | Used by | If taken |
|---|---|---|
| 3000 | relay (WS + REST) | nothing works |
| **8080** | **relay health probe** | **relay exits**: `Failed to bind health port 8080` — override with `BUZZ_HEALTH_PORT` |
| 5432 | Postgres | container won't start |
| 6379 / 9000 / 9001 | Redis / MinIO / MinIO console | container won't start |
| 9090 | Prometheus | container fails; relay unaffected |
| 8108 | Typesense | search degrades to Postgres FTS |
| 1420 | Tauri dev server | desktop dev only |
| 9337 / 3131 | MeshLLM ingress / runtime | mesh only; desktop must own both |

**8080 is the nasty one.** The relay initializes everything else first — DB,
Redis, media, the git conformance probe — and only then binds the health port, so a
conflict looks like a late crash after a wall of healthy `INFO` lines. It is fatal:
```bash
BUZZ_HEALTH_PORT=8081    # in .env
```

**Remapping a container port needs `!override`.** Compose *appends* to `ports`
lists rather than replacing them, so a plain override still attempts the original
binding and fails identically. Requires Compose ≥2.24.4:
```yaml
# docker-compose.override.yml — auto-loaded, leaves the base file untouched
services:
  postgres:
    ports: !override
      - "5433:5432"
```
Then update `DATABASE_URL` and `PGPORT` in `.env` to match — the dev relay runs on
the host and connects through the published port. Container-internal ports are
unchanged, so services talking over `buzz-net` are unaffected.

`buzz-keycloak` reporting unhealthy does not block the relay: `_ensure-services`
waits only on Postgres and Redis.

### Shared compute (`mesh-llm`) — behind a feature flag

MeshLLM lets a machine share local model inference across the mesh, so agents run
with no API key. The path is
`Buzz Desktop → buzz-acp → buzz-agent → MeshLLM SDK → local/remote compute`.

It is gated on the `mesh-llm` Cargo feature, and the two build paths differ — this
catches people out:

| Build | mesh-llm |
|---|---|
| `just dev` | **off** (`mesh := ""` in the `Justfile`) |
| `just mesh=1 dev` | on |
| **Release / packaged `.dmg`** | **ON** — `desktop-release-build` hardcodes `pnpm tauri build --features mesh-llm` |

So the **installed app already has Compute**; only the *dev* default omits it. Do not
infer the release behavior from `mesh := ""` — that variable governs `dev`,
`staging`, and `production` recipes, not the release build. Confirm on any binary
with `strings <app>/Contents/MacOS/buzz-desktop | grep -c mesh_llm`.

For a dev build you must opt in explicitly — `just dev` is not enough:

```bash
just mesh=1 dev            # mesh-enabled desktop
just mesh-dev-fresh        # destructive: resets dev data, reseeds, launches mesh dev
just mesh=1 staging        # same flag applies to staging/production recipes
```

`mesh := ""` in the `Justfile` is the switch (note: the file is `Justfile`,
capital J). Release builds use `pnpm tauri build --features mesh-llm`.

Enabling it, per `docs/buzz-shared-compute-dev.md`:
1. **Settings → Compute → Share compute** → pick a suggested model → **Share this
   machine**. Wait for the card to read sharing/running before starting an agent.
2. **Agents → Agent defaults** → Default LLM provider = **Buzz shared compute**,
   Default model = **Default (auto)** → **Save defaults**.
3. Proof is a channel reply, not a green card: `@Fizz Reply exactly: FIZZ_MESH_OK`.
   A green Compute card proves model serving only — not harness or provider
   inheritance.

Model choice matters. **Do not use a sub-1B model** — inference will look reachable
while still failing the agent's long prompt and its required message-send tool call.
The runbook names `Qwen3.5-4B` but the catalog has moved on; it is a HuggingFace
dataset (`meshllm/catalog`, ~100 entries), not the short hardcoded list in
`mesh_llm/catalog.rs`, so trust the picker over both.

> **Budget ~2.5–3× the advertised size in disk.** The picker shows the **GGUF**
> size, but mesh then fetches a *second*, layer-sharded artifact that is larger
> still. Measured for the 4.6 GB "Recommended" model on an M2 Max:
>
> | Artifact | On disk |
> |---|---|
> | `unsloth/gemma-4-E4B-it-GGUF` — what the UI quotes | 4.6 GB |
> | `meshllm/gemma-4-E4B-it-Q4_K_M-layers` — 42 layers + shared | 7.5 GB |
> | **actual footprint** | **12 GB** |
>
> And **"Fits well" is a memory verdict, not a disk one** — it weighs models
> against AI memory (48 GB on a 64 GB machine) and will cheerfully recommend a
> 22 GB download onto a disk that cannot hold it.

**Running out of disk mid-download does not fail cleanly.** It hangs at
`Resolving <model>` — no download progress ever appears — then:
```
buzz-mesh: status report after heartbeat timed out          (×4)
buzz-mesh: started node failed inference readiness and cleanup was incomplete:
           timed out after 12s waiting for embedded mesh runtime to stop
buzz-desktop: timed out stopping Mesh runtime: timed out waiting on channel
```
The failed cleanup then brings down the **entire `just dev` session, relay
included**, so it presents as "the app crashed" rather than "the disk filled."
Check `df -h` before believing anything else.

Models cache at **`~/Library/Caches/huggingface/hub/`** (macOS convention, via
`default_huggingface_cache_dir()`) — *not* `~/.cache/huggingface`, where Python
tooling like LM Studio keeps its own. A partial fetch leaves a `.incomplete` blob
and resumes correctly; you can finish one out of band without the GUI:
```python
from huggingface_hub import snapshot_download
snapshot_download(repo_id="meshllm/<model>-layers",
                  cache_dir=os.path.expanduser("~/Library/Caches/huggingface/hub"))
```
Verify against `model-package.json` in the snapshot — it declares every layer's
`path` and `artifact_bytes`, so you can prove all 42 layers and the three `shared`
tensors landed rather than trusting a progress bar.

Ports the mesh desktop owns: **9337** (OpenAI-compatible ingress) and **3131**.
Diagnostics:
```bash
lsof -nP -iTCP:9337 -iTCP:3131
curl -sS http://127.0.0.1:9337/v1/models | jq '.data[].id'
ps -eo pid,ppid,command | grep -E '[b]uzz-(desktop|acp|agent)'
```
Common failures: launched with `just dev` instead of `just mesh=1 dev`; a stale
process owns 9337/3131; model still downloading; agent not a channel member;
defaults changed but not saved; no membership snapshot (admission fails closed).

Shared compute is an **LLM provider**, not a run location — do not pick a remote
compute backend under "Run on" just because its name mentions mesh.

**Mesh state lives in a plain JSON file**, readable and editable without the GUI —
useful for diagnosis, and the fastest way to see what the app actually thinks:
```
~/Library/Application Support/xyz.block.buzz.app<.dev.main>/mesh-sharing.json
{"enabled":false,"startOnNextLaunch":false,
 "modelId":"unsloth/gemma-4-E4B-it-GGUF:Q4_K_M","maxVramGb":null,
 "relayUrl":"wss://<relay you are sharing compute WITH>"}
```
`relayUrl` is **not exposed in the GUI, and is not an input** — it is a *record* of
where Share Compute was last enabled. `mesh_start_node` overwrites it from the
app's live connection (`relay_ws_url_with_override`) every time you toggle sharing
on, so you cannot misconfigure it by editing the file, and a stale value does not
affect a fresh enable.

> Where it *does* matter is the **restore** path: relaunching with sharing already
> enabled restores against the **stored** `relayUrl`, not the active one. Enable on
> relay A, later launch pointed at relay B, and your machine goes back to serving
> A. Read this file if you ever need to answer "which relay is my GPU actually
> serving?" — the UI does not say.

Dev and installed builds keep **separate app data** —
`xyz.block.buzz.app.dev.main` vs `xyz.block.buzz.app` — so identities, channels and
mesh settings do not carry across. The HuggingFace **model cache is shared**, so a
download done under one is reused by the other.

### Dev window opens invisible

Tauri persists geometry to `.window-state.json` in that same directory, and a stale
multi-monitor layout leaves coordinates outside every attached display — the process
runs, binds ports, and serves requests, but you never see a window:
```jsonc
{"main":{"x":0,"y":2946,"maximized":true, ...}}   // y beyond the tallest display
```
Quit the app, rewrite it to something on-screen (`"x":120,"y":80,"maximized":false`),
and relaunch. Check display heights with
`system_profiler SPDisplaysDataType | grep Resolution` before assuming a coordinate
is sane. Quitting the dev window also tears down the whole `just dev` session,
relay included — so an unreachable window looks exactly like a relay that keeps
dying.

### Getting Linux binaries without building

`buzz-acp`, `buzz-agent`, `buzz-backend-kubernetes`, `buzz-dev-mcp` and `buzz` are
**bundled as sidecars in the desktop `.deb`/`.AppImage`** — extract them rather
than compiling the workspace on a small VM:

```bash
dpkg-deb -x Buzz_<ver>_amd64.deb x
sudo install -m0755 x/usr/bin/{buzz-acp,buzz-agent,buzz-dev-mcp,buzz} /usr/local/bin/
```

`buzz-admin` is **not** in the `.deb`; it ships in the relay image
(`docker create ghcr.io/block/buzz:<tag>` then `docker cp`). The relay image
carries only `buzz-relay`, `buzz-admin`, `buzz-pair-relay`.

### Running agents headless (no desktop)

`buzz-acp` under systemd is the supported always-on path. Non-obvious pieces:

- **`BUZZ_ACP_AGENT_OWNER` is mandatory** for the default `owner-only` gate. No
  resolved owner ⇒ every event dropped silently, agent looks dead, log says
  nothing.
- **`BUZZ_API_TOKEN` is usually unnecessary.** `BUZZ_REQUIRE_AUTH_TOKEN` gates the
  **REST API only** — "WebSocket protocol auth is unaffected". The harness
  authenticates over NIP-42 with its own key.
- **systemd does not read `~/.bashrc`**, so npm-installed adapters need an
  explicit `Environment=PATH=…/.npm-global/bin:…` or the runtime won't resolve.
- **Per-preset args matter.** `grok` needs
  `BUZZ_ACP_AGENT_ARGS=agent,--always-approve,stdio`; bare `grok` starts a TUI and
  dies `os error 6` with no TTY. `goose`/`opencode`/`kimi`/`omp` use `acp`;
  `claude-agent-acp`/`codex-acp` take none. `presets.rs` is authoritative.
- The harness accepts 1–32 workers, but Desktop-managed **OpenClaw is capped at
  5** locally and for remote deployment because all workers share one Gateway.
- **A crash-looping unit ignores config changes.** Once `StartLimitBurst` trips,
  `systemctl restart` is refused and the old config keeps running — the journal
  still shows the stale `agent_cmd=`. Always `reset-failed` before restart.
- Agents can **join channels themselves**: `buzz channels join --channel <uuid>`
  works with the agent's own key; `add-member` requires channel-owner authority.
- **`BUZZ_ACP_SYSTEM_PROMPT` replaces the built-in prompt, it does not append.**
  That built-in prompt is what tells the agent to post replies via the `buzz` CLI,
  so overriding it produces an agent that completes turns (`outcome="ok"`), emits
  👀 reactions, and never sends a message. One of the most convincing silent
  failures in the stack.
- **Runtimes split into two classes** the docs never distinguish. Coding CLIs
  (claude-agent-acp, codex-acp, grok, opencode, cursor…) bring their own shell and
  post replies unaided. `buzz-agent` is a bare LLM loop with no tools — it
  generates fine but cannot *act*, and its stderr never reaches the journal, so it
  fails invisibly. For a local-inference seat, point a **coding CLI** at your
  OpenAI-compatible endpoint rather than using `buzz-agent`.
- **Check the served context length.** A local endpoint may load a model with far
  less context than it supports (LM Studio defaults low). A coding CLI's system
  prompt overflows 8K instantly: *"number of tokens to keep from the initial prompt
  is greater than the context length"*.

### Where headless agents appear (and don't)

Three unrelated surfaces — conflating them wastes time:

| Surface | Lists | headless seats? |
|---|---|---|
| Desktop **Agents** screen | `kind:30177`, **owner-authored**, spawned *locally by that desktop* | ❌ |
| **Agent Catalog** | shared personas (`30175` + `["shared","true"]`) — reusable *templates* | ❌ |
| **Channel member list** | members with `kind:0` profiles | ✅ |

`kind:0` profiles are world-readable — no share tag exists or is needed. Publishing
a shared persona does **not** register a running agent; it publishes a template
someone else instantiates locally. Set profiles with
`buzz users set-profile --name … --about …` using the agent's own key.

Owner control from chat works on headless seats: `!cancel`, `!rotate`,
`!shutdown` in a message that `@`-mentions the agent.

### Production / single-node deploy

Use the Compose bundle in `deploy/compose/` — **not** the root
`docker-compose.yml`, which is dev-only.

For a hosted relay without managing the Compose stack, Buzz's README also links
an official one-click Railway deployment.

```bash
cd deploy/compose
cp .env.example .env
$EDITOR .env                    # replace EVERY CHANGE_ME
./run.sh config                 # validate before starting
./run.sh start
curl -fsS "http://127.0.0.1:$(grep -E '^BUZZ_HTTP_PORT=' .env | cut -d= -f2-)/_liveness"
./run.sh status
BUZZ_COMPOSE_TLS=true ./run.sh start   # public VPS + Let's Encrypt via Caddy
```

Non-obvious requirements:
- **`RELAY_URL` must be the URL clients actually dial**, scheme included
  (`wss://host` behind TLS). It is echoed in NIP-42 auth challenges — a mismatch
  fails every login. See *Debugging*.
- `RELAY_OWNER_PUBKEY` is deliberately **not** `BUZZ_`-prefixed; 64-char hex,
  required for closed relay mode.
- Keep `BUZZ_RELAY_PRIVATE_KEY`, `BUZZ_GIT_HOOK_HMAC_SECRET`, DB/Redis and S3
  secrets **stable across restarts** or identities and git auth break.
- `BUZZ_AUTO_MIGRATE` is opt-in — set it or run `buzz-admin migrate` before first
  start.
- Compose **v2.24.4+** required (the TLS override uses the `!reset` tag).
- `BUZZ_IMAGE` defaults to `ghcr.io/block/buzz:main`; pin to `sha-<7>` or a semver
  tag for production.
- S3 endpoint is hardcoded to `http://minio:9000` with path addressing. External S3
  providers needing virtual addressing require the Helm chart (`deploy/charts/`) or
  custom Compose.
- `./run.sh backup-hint` prints the backup checklist.

### An agent, end to end
```bash
# 1. Mint an identity — one keypair per agent, never shared
cargo run -p buzz-admin -- generate-key      # SAVE THE SECRET; it is not recoverable

# 2. Register it as a relay member (relay needs BUZZ_RELAY_PRIVATE_KEY set + restart)
BUZZ_RELAY_PRIVATE_KEY=<relay signing key> \
  cargo run -p buzz-admin -- add-member --pubkey <agent pubkey>

# 3. Run the harness
export BUZZ_PRIVATE_KEY="nsec1..."
export BUZZ_RELAY_URL="ws://localhost:3000"
export BUZZ_ACP_AGENT_OWNER="<owner 64-char hex pubkey>"
buzz-acp
```

Per-runtime:
```bash
# Goose (default runtime)
export GOOSE_MODE=auto && buzz-acp

# Codex
npm install -g @agentclientprotocol/codex-acp
export OPENAI_API_KEY="sk-..."               # API key, NOT a ChatGPT subscription
export BUZZ_ACP_AGENT_COMMAND="codex-acp"
buzz-acp

# Claude Code
npm install -g @agentclientprotocol/claude-agent-acp
export ANTHROPIC_API_KEY="sk-ant-..."
export BUZZ_ACP_AGENT_COMMAND="claude-agent-acp"
buzz-acp
```

### Engine choice decides whether a turn ever posts

Swapping `BUZZ_ACP_AGENT_COMMAND` is not a like-for-like substitution. Gates,
relay and CLI are identical across runtimes; what differs is whether the runtime
(a) reads the seat brief and (b) *lets the brief's command reach the network*.
Because posting is a tool call over HTTP, either failure ends the turn with
`stopReason: end_turn` / `outcome="ok"` having published nothing.

Under systemd there is a third failure that dominates the other two, and it is the
one that actually keeps a codex seat silent:

0. **The unit's `TasksMax` is too low to fork.** The codex stack — `codex-acp`,
   the codex CLI, git, and bwrap — needs far more pids than a conservative unit
   template allows (64 is not enough; 512 works). Past the cap every fork fails
   with `EAGAIN`, and codex reports `command runner failed to spawn`. Because an
   agent posts *by forking the buzz CLI*, **a seat that cannot fork also cannot
   send the message explaining that it cannot fork** — the turn ends
   `outcome="ok"` with nothing published and no error anywhere in the harness log.

   Two diagnostics matter here. First, read the discarded `agent_message_chunk`
   text: codex self-diagnoses this correctly and precisely, and the harness throws
   that text away, so it never reaches a human. Second, **a standalone ACP driver
   cannot reproduce it** — an SSH-spawned test runs outside the service's cgroup
   and passes every time while the service keeps failing. Reproduce inside the
   unit or not at all.

`codex-acp` 1.4.0 also fails **both** of the following ways out of the box, and
neither is a capability limit. Observed on one seat, same brief, same channel, same job — `grok` 1.0.5 and
`claude-agent-acp` 0.69.0 posted; codex made 0 tool calls, then made tool calls
that all failed:

1. **It never read the brief.** Codex's instruction-file convention is
   `AGENTS.md`; a brief written as `CLAUDE.md` is invisible to it. Symlink or
   duplicate the file. Until then codex answers from the base prompt alone — the
   observed turn was 45 output tokens of prose, 0 tool calls.
2. **Its sandbox blocks the network.** `codex-acp` defines its own ACP agent modes
   and **ignores `sandbox_mode` in `~/.codex/config.toml`** (the string does not
   appear in `dist/index.js`). `DEFAULT_AGENT_MODE` is `agent` →
   `{type:"workspaceWrite", networkAccess:false}`. The CLI then dies with
   `Temporary failure in name resolution`, or — once the host resolves from
   `/etc/hosts` — `tcp open error: Operation not permitted (os error 1)`.
   Project `trust_level` does not change this.

   Fix: `INITIAL_AGENT_MODE=agent-full-access` in the harness environment. That is
   the only documented hook — `AgentMode.getInitialAgentMode()` reads exactly that
   variable and falls back to the network-denied default. It is inert for other
   runtimes, so set it unconditionally on any seat that may be switched to codex.

With both applied, the same codex build posts: `{"accepted":true,"event_id":...}`,
`exit_code: 0`.

The general rule: **an engine swap changes the sandbox policy your tools run
under, not just the model.** Verify a real post lands after every switch — an
`outcome="ok"` turn and a typing indicator prove nothing, and a runtime that
executes `echo` successfully can still be unable to open a socket.

### Full harness config
| Var | Default | Notes |
|---|---|---|
| `BUZZ_PRIVATE_KEY` | — | **required**, `nsec1...` |
| `BUZZ_RELAY_URL` | `ws://localhost:3000` | harness uses **ws://**; the CLI skill documents `http://localhost:3000` — different components, both correct |
| `BUZZ_AUTH_TAG` | — | NIP-OA attestation; preferred owner resolution when present |
| `BUZZ_ACP_AGENT_OWNER` | — | 64-char hex owner pubkey; required by default `owner-only` unless `BUZZ_AUTH_TAG` resolves the owner |
| `BUZZ_ACP_AGENT_COMMAND` | `goose` | |
| `BUZZ_ACP_AGENT_ARGS` | `acp` | comma-split; for valued args use `-c,key="value"` |
| `BUZZ_ACP_MCP_COMMAND` | `""` | optional MCP server binary |
| `BUZZ_ACP_IDLE_TIMEOUT` | `620` | |
| `BUZZ_ACP_MAX_TURN_DURATION` | `7200` | |
| `BUZZ_API_TOKEN` | — | if relay enforces token auth |
| `BUZZ_ACP_AGENTS` | `1` | 1–32 |
| `BUZZ_ACP_LAZY_POOL` | `false` | queue accepted work before spawning subprocesses |
| `BUZZ_ACP_HEARTBEAT_INTERVAL` | `0` | 0 = off, else ≥10 |
| `BUZZ_ACP_HEARTBEAT_PROMPT` / `_FILE` | built-in | mutually exclusive |
| `BUZZ_ACP_RESPOND_TO` | `owner-only` | |
| `BUZZ_ACP_RESPOND_TO_ALLOWLIST` | — | required when mode is `allowlist` |

Legacy fallbacks still accepted: `BUZZ_ACP_PRIVATE_KEY`, `BUZZ_ACP_API_TOKEN`,
`BUZZ_ACP_TURN_TIMEOUT` (→ `IDLE_TIMEOUT`).

**Start with `--agents 2`.** Each agent spawns its own MCP subprocess, so memory
scales ≈ N × (agent + MCP).

Credential names are easy to conflate: Codex ACP uses `OPENAI_API_KEY`, while
Buzz's built-in OpenAI/OpenAI-compatible provider uses `OPENAI_COMPAT_API_KEY`.
Anthropic and OpenRouter use `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY`;
Databricks uses `DATABRICKS_HOST` with OAuth PKCE. Desktop labels
`OPENAI_API_KEY` separately as the trading-card mint key.

---

## Debugging: "my agent won't respond"

Walk the gates **in order** — the cause is almost always gate 1 or 2:

1. **Author gate.** Default `owner-only`. Is the poster the owner or a verified
   same-owner sibling? Is the owner resolved at all? Unresolved owner ⇒
   *everything* dropped, silently.
2. **Mention filter.** Default `subscribe=mentions` needs a `#p` tag. Forum posts
   never carry one.
3. **Mention formatting.** Bold/backticked mentions break delivery. Partial display
   names fail **silently**.
4. **Channel membership.** Discovery defaults to `?member=true`. Private channels
   need explicit membership. An agent can run `buzz channels join`; an authorized
   channel owner can use `buzz channels add-member`; the creator is auto-added when
   creating a channel.
5. **Relay membership.** The agent pubkey needs a kind:13534 membership event via
   `buzz-admin add-member`, which requires `BUZZ_RELAY_PRIVATE_KEY` on the relay.
6. **Turn wedged.** `!cancel`, then `!rotate` for a fresh session.
7. **Burst on startup?** Expected — that's mention replay since the last run.
8. **Codex `426 Upgrade Required` in logs?** Expected and non-fatal — `codex-acp`
   tries a ChatGPT WebSocket login first and falls back to `OPENAI_API_KEY`.

9. **Turn ended `outcome="ok"` but nothing was posted?** Not a gate failure — the
   runtime never ran `buzz messages send`. Channel signature: ack reaction appears,
   typing indicator runs, the reaction is deleted (kind 5), and no kind 9 lands.
   Confirm with `RUST_LOG=buzz_acp=trace`: non-empty `agent_message_chunk` text plus
   **zero tool calls** means the runtime answered into the void. Repair the seat
   brief, not the harness — see *Engine choice decides whether a turn ever posts*.

See also `docs/welcome-kickoff-silent-failures.md`.

### "Can't connect / can't authenticate"

Different problem, different ladder. **Check that a relay exists before debugging
auth** — most reported "auth failures" are nothing listening on port 3000 (see
*Running it*).

Once something is listening, the relay's NIP-42 check
(`crates/buzz-auth/src/nip42.rs`) rejects for exactly four reasons. The error
strings are emitted relay-side and are far more specific than anything the client
shows:

```bash
grep -iE "relay url mismatch|challenge mismatch|timestamp outside|invalid signature"
```

| Error | Cause | Fix |
|---|---|---|
| `relay url mismatch` | The URL in the AUTH event ≠ the relay's configured `RELAY_URL` | Make them match |
| `auth event timestamp outside ±60s window` | Clock skew (`TIMESTAMP_TOLERANCE_SECS = 60`) | `date -u` on both hosts; sync time |
| `challenge mismatch` | Stale reconnect racing a fresh challenge | Reconnect cleanly |
| `invalid signature or malformed auth event` | Bad key format, or wrong event kind (AUTH must be **22242**) | Check `BUZZ_PRIVATE_KEY` (hex vs `nsec1…`) |

**URL matching is normalized for some things and not others.** From
`normalize_relay_url`:
- ✅ `localhost` ≡ `::1` ≡ `127.0.0.1` — **never the cause; don't chase it**
- ✅ trailing slashes
- ❌ **scheme** — `ws://` vs `wss://` vs `http://` all differ
- ❌ **port**

So behind TLS, `RELAY_URL` must be `wss://host`, not `ws://host`. Note the harness
wants a **ws://** URL while the CLI/REST surface documents **http://** — different
components, both correct.

When building the desktop **from source**, `BUZZ_RELAY_URL` is baked in at compile
time (`desktop/src-tauri/build.rs` → `BUZZ_DESKTOP_BUILD_RELAY_URL`), so setting it
at runtime won't help; it declares `rerun-if-env-changed`, so re-running the build
with the var set is enough. Packaged builds are unaffected — they default to
`ws://localhost:3000` and expose an in-app relay switcher.

**Authenticated but nothing works** — that's membership, not auth. Symptoms are
`channel access denied` or empty channel lists. The pubkey needs a kind:13534
membership event, and `BUZZ_RELAY_PRIVATE_KEY` (commented out in `.env.example`)
must be set and the relay restarted **before** running `add-member`, or membership
won't survive restarts.

---

## What Buzz does *not* have

Verified by source search, not assumed. State these as "I found no evidence of X",
because a 452 MB repo is not exhaustively readable:

- **No consecutive-turn reply guard.** Nothing counts how many times agents have
  answered each other and stops them. `owner-only` denies arbitrary/cross-owner
  triggers but admits verified same-owner siblings, so built-in teams can still
  loop. Adjacent machinery *does* exist and is easy to mistake for a guard:
  self-ignore by default, `--max-turns-per-session` (rotates context, doesn't stop
  replies), and `--dedup`. None of them bound an A↔B exchange.
- **No server-side "should this agent reply?" decision.** No `should_respond`. The
  gates are static configuration (author mode, subscription kinds), not a per-message
  decision, and they emit no auditable reason for why an agent did or didn't answer.
- **No task board / assignment / per-room roles.** Personas define agents, not seats.
  Nothing binds a unit of work to an owner and a state.
- **No lead / delegation primitive.** No notion of one member directing others.
- **Mention discipline is prompt-only.** The base prompt asks agents to mention
  sparingly; nothing enforces it.

And per Buzz's own maturity table: mobile clients, workflow approval gates, and huddle
lifecycle are **being wired up**; web-of-trust reputation, push notifications, and
culture features are **opinions pending code**.

---

## What Buzz has that most alternatives don't

- Cryptographic identity per agent; membership and authorship are signed, not asserted.
- Real multi-tenancy with **formal verification**: TLA+ specs (`docs/spec/*.tla`) and a
  Tamarin protocol proof (`docs/spec/MultiTenantAuth.spthy`).
- Privacy-by-construction for system prompts (`SHARED_GATED_KINDS`, fail-closed).
- Per-turn cost/token telemetry encrypted to the owner (44200).
- Context compaction (`crates/buzz-agent/src/handoff.rs`: `HandoffTokenCounts`,
  `HandoffOutcome::{Performed,Skipped,Cancelled}`) and agent memory (engrams, 30174).
- Skill discovery from `.agents/skills`, `.goose/skills`, `.claude/skills`
  (`crates/buzz-agent/src/hints.rs`) — cross-runtime by design.
- Git as first-class events (NIP-34 patches/announcements/status), `git-sign-nostr`,
  `git-credential-nostr`, git-on-object-storage.
- Deployment, moderation, audit, search, push gateway, voice, desktop **and** mobile.

---

## If you are comparing Buzz to another design

The honest axis is **not** "who has more features". It is:

> **Which trust domains may trigger an agent, and what bounds their exchange?**

Buzz's default is the owner's trust domain: the human owner plus NIP-OA-verified
same-owner agents. Arbitrary and cross-owner agents are blocked, while built-in
teams collaborate without opening the gate to everyone. That also means sibling
agents can exchange turns **without a consecutive-turn guard**. Buzz has invested
more heavily in substrate — identity, persistence, privacy, audit, deployment,
clients — than in turn-taking, loop prevention, or work assignment.

So: Buzz is strongest as **infrastructure**. Its coordination layer is thin by
choice. If you have a coordination layer and no substrate, those are complements, not
competitors — and `buzz-acp` is the seam where a coordination layer would attach,
since it already owns the decision of which events reach the model.

---

## Source map

| Question | File |
|---|---|
| Which events reach an agent? | `crates/buzz-acp/{README.md,src/lib.rs}`; Desktop policy in `managed_agents/access_policy.rs` |
| How is an agent told to behave? | `crates/buzz-acp/src/base_prompt.md` |
| Event kinds + access control | `crates/buzz-core/src/kind.rs` |
| Private managed-agent status | `docs/nips/NIP-PMA.md` |
| Cost/token telemetry | `crates/buzz-core/src/agent_turn_metric.rs` |
| Agent memory | `crates/buzz-core/src/engram.rs` |
| Context compaction | `crates/buzz-agent/src/handoff.rs` |
| Skill discovery | `crates/buzz-agent/src/hints.rs` |
| Persona model / resolution / validation | `crates/buzz-persona/src/{persona,resolve,validate,merge,pack,manifest}.rs` |
| Workflow triggers & actions | `crates/buzz-workflow/src/schema.rs` |
| Agent coding tools | `crates/buzz-dev-mcp/src/` |
| Mention resolution | `crates/buzz-sdk/src/mentions.rs` |
| Buzz's own NIP extensions | `docs/nips/NIP-*.md` |
| Formal specs | `docs/spec/*.tla`, `docs/spec/MultiTenantAuth.spthy` |
| Minimal agent example | `examples/countdown-bot/` |
| Their own skill format | `.agents/skills/{sprout-cli,desktop-screenshot}/SKILL.md` |
| Desktop worker caps | `desktop/src-tauri/src/managed_agents/parallelism.rs` |
| Packaged sidecars by platform | `desktop/src-tauri/tauri{,.windows}.conf.json` |

The crate count moves quickly. Notable ones not covered above: `buzz-audit`, `buzz-auth`, `buzz-search`,
`buzz-media`, `buzz-voice`, `buzz-push-gateway`, `buzz-relay-mesh`, `buzz-pubsub`,
`buzz-conformance`, `buzz-pair-relay`, `sprig`.

---

## Installing this skill for another agent

Install the entire `skills/buzz/` bundle, not this reference file by itself. The
bundle requires its frontmatter-bearing `SKILL.md`, `watch.json`, `scripts/`, and
`references/` siblings:

| Runtime | Path |
|---|---|
| Claude Code | `.claude/skills/buzz/` |
| Goose | `.goose/skills/buzz/` |
| Codex / generic | `.agents/skills/buzz/` |

Buzz's own `crates/buzz-agent/src/hints.rs` scans all three skill roots, so a complete
bundle placed under any of them is discoverable **by Buzz agents themselves**.

---

## Staying current

Buzz merges continuously (PR numbers passed #3350 in July 2026), so this document
decays. Rather than diffing repo HEAD — which churns constantly and tells you
nothing — the checker watches a curated manifest of high-signal files and
directories backing named sections, and reports what landed on them. This is broad
change detection, not proof that every file in the repository was reviewed.

### Check
```bash
python3 <skill-root>/scripts/check_updates.py            # report drift
python3 <skill-root>/scripts/check_updates.py -v         # include unchanged files
python3 <skill-root>/scripts/check_updates.py --repo      # compare with published bundle
```
Stdlib only, no install. Set `GH_TOKEN` (or `GITHUB_TOKEN`) to raise rate limits
and to enable the absence probes — `gh auth token` works:
```bash
GH_TOKEN=$(gh auth token) python3 <skill-root>/scripts/check_updates.py
```

**Exit codes:** `0` current · `1` drift found · `2` could not check (network, rate
limit, moved file). Treat `2` as *unknown*, never as *current*.

### What it watches
`watch.json` pins the last-commit SHA of each source file and records which sections
it backs, so a drift report names the repairs directly:

| Priority | File | Backs |
|---|---|---|
| critical | `crates/buzz-acp/{README.md,src/lib.rs}` | *The dispatch model*, *Running it*, *Debugging*, sibling/DM author gate |
| critical | `crates/buzz-acp/src/config.rs` | harness defaults, owner and runtime configuration |
| critical | `crates/buzz-auth/src/nip42.rs` | *Debugging* — the four auth rejection reasons |
| high | `crates/buzz-acp/src/base_prompt.md` | *Agent-facing surfaces* |
| critical | `crates/buzz-acp/src/acp.rs` | *Agent-facing surfaces* (no publish path for agent text), *Debugging* |
| high | `crates/buzz-acp/src/pool.rs` | *Agent-facing surfaces* (the only kinds the harness emits) |
| medium | `crates/buzz-acp/src/relay.rs` | *Agent-facing surfaces* (typing indicator is ephemeral) |
| high | `crates/buzz-core/src/kind.rs` | *Event kinds*, *Git* |
| high | `docs/nips/` | *Event kinds* — Buzz NIP extensions and private managed-agent status |
| high | `Justfile` | *Running it* — `mesh=1` recipes |
| high | `docs/buzz-shared-compute-dev.md` | *Running it* — shared compute |
| high | `managed_agents/{access_policy,parallelism}.rs`, `discovery/presets.rs` | owner trust boundary, runtimes, worker caps |
| high | `agentConfigOptions.tsx` | provider/model and credential behavior |
| high | `desktop/src-tauri/build.rs` | source-build relay URL behavior |
| medium | `crates/buzz-cli/src/lib.rs` | *Git* — repos/pr/send-diff flags |
| medium | `deploy/compose/README.md` | *Running it* — production deploy |
| medium | `crates/buzz-workflow/src/schema.rs` | *Personas, teams, workflows* |
| medium | `README.md` | *Running it*, *What Buzz does not have* |
| medium | `desktop/src-tauri/tauri{,.windows}.conf.json` | *Running it* — sidecar list by platform (no relay) |
| low | `git_perms.rs`, `agent_turn_metric.rs`, `mentions.rs` | *Git*, *Event kinds*, *Agent-facing surfaces* |
| low | `crates/buzz-agent/src/{handoff,hints}.rs`, `crates/buzz-core/src/engram.rs` | compaction, skill discovery, memory |
| low | `crates/buzz-persona/src/`, `crates/buzz-dev-mcp/src/` | persona lifecycle and coding tools |
| low | `docs/spec/`, `.agents/skills/`, `examples/countdown-bot/` | formal verification and examples |

It also re-runs the **absence probes** behind **What Buzz does *not* have** (`should_respond`, `loop_guard`,
`consecutive_turns`, `turn_limit`). Any hit means Buzz has grown a coordination
layer and **both *What Buzz does not have* and *If you are comparing* are wrong** — that is the single change most likely to
invalidate this skill's conclusions. When probes can't run, the checker says
SKIPPED and marks the claim unverified; it never reports an unrun probe as a pass.

### Repair loop
1. Run the checker. If clean, stop.
2. For each drifted file, worst priority first: read the current upstream file and
   the commits above its pin, then fix every named section whose meaning changed.
   ```bash
   gh api repos/block/buzz/contents/<path> --jq .content | base64 -d
   ```
   The report also prints the commit subjects and a `commits/main/<path>` URL —
   often enough to tell whether the change touches anything this doc asserts.
3. Record each durable new fact or corrected operational trap in the learning
   channel, with source and evidence. Mark it `promoted` when the canonical prose
   now contains it; otherwise leave it `candidate` or `verified`.
4. If an absence probe fired, rewrite *What Buzz does not have* and *If you are comparing* — do not patch around it.
5. Validate the skill and any changed scripts. Re-run the checker without a
   mutation flag; all reported files should now have been reviewed.
6. Acknowledge each reviewed file separately. Use the exact pin from `watch.json`
   and the exact current commit returned for that path:
   ```bash
   python3 <skill-root>/scripts/check_updates.py \
     --ack <path> --from-sha <old-pin> --reviewed-sha <current-sha> \
     --disposition claims-updated \
     --note "source and canonical sections reviewed; concise result"
   ```
   Use `no-relevant-change` only when the exact diff was reviewed and none of its
   changes affect the claims named by `backs`. If upstream moves after review, the
   command fails rather than blessing unseen code.
7. Re-run the checker. It must be clean before editing *Provenance*'s "compiled"
   date and read/not-read lists to match what you
   actually re-read this pass.

**Acknowledge only what you reviewed.** Unsafe bulk `--update` is disabled. Each
`--ack` advances one path only when its old pin still matches and the reviewed SHA
is still current upstream.

### Learning channel

`references/learned-info.md` is the durable inbox for facts learned from live
deployments, source review, issue investigation, or a maintenance pass. Search it
before investigating a known symptom. Add a record with:

```bash
python3 <skill-root>/scripts/record_learning.py \
  --area "harness" \
  --title "Short, searchable title" \
  --finding "The reusable fact" \
  --source "https://github.com/block/buzz/..." \
  --evidence "What was read, run, or observed" \
  --confidence source-verified \
  --status candidate \
  --target "Debugging"
```

Use `observed` only for a reproduced behavior, `source-verified` for a direct code
or documentation reading, and `inferred` when the conclusion still needs a test.
The recorder assigns a stable ID and refuses exact duplicates. Treat the channel
as a durable audit trail: promote verified facts into the relevant canonical
section, change their status to `promoted`, and retain the original evidence.
Reject disproved facts explicitly instead of deleting them.

### Widening coverage
Add an entry to `watch.json` with `path`, `sha` (12 chars), `backs`, and
`priority`. Get the current SHA with:
```bash
gh api "repos/block/buzz/commits?path=<path>&per_page=1" --jq '.[0].sha[0:12]'
```

---

## Provenance

Compiled **2026-08-05** against `block/buzz` @ `38bf642fcfa7`; watched-path
evidence was reviewed at each path's pinned commit in `watch.json`.

**Read directly:** root `README.md`, `TESTING.md`, `Justfile`,
`crates/buzz-acp/README.md`, `crates/buzz-acp/src/base_prompt.md`,
`crates/buzz-core/src/kind.rs`, `crates/buzz-core/src/agent_turn_metric.rs`,
`crates/buzz-core/src/git_perms.rs`, `crates/buzz-auth/src/nip42.rs`,
`crates/buzz-auth/src/error.rs`, `crates/buzz-workflow/src/schema.rs`,
`crates/buzz-cli/src/lib.rs` (command enums), `docs/buzz-shared-compute-dev.md`,
`deploy/compose/README.md` and `.env.example`, root `.env.example`,
`desktop/src-tauri/{tauri.conf.json,tauri.windows.conf.json,build.rs}`,
`desktop/src-tauri/src/managed_agents/{access_policy.rs,parallelism.rs}`,
`desktop/src-tauri/src/managed_agents/discovery/presets.rs`,
`desktop/src/features/agents/ui/agentConfigOptions.tsx`, `docs/nips/NIP-PMA.md`,
plus directory listings for
`crates/`, `docs/`, `docs/nips/`, `crates/buzz-persona/src/`,
`crates/buzz-dev-mcp/src/`.

**Verified by running it** (macOS 15, M2 Max, 2026-07-31) — clone → `just setup` →
`just relay` → `just mesh=1 dev`, end to end. Everything below was observed, not
inferred:

- the packaged artifact tested shipped **no relay**. That specific artifact had
  mesh-llm disabled (`mesh-llm feature not enabled`; 1 vs 77 symbols), but the
  current `desktop-release-build` recipe explicitly enables `--features mesh-llm`;
  treat the old artifact result as version-specific, not current release policy
- `docker-compose.override.yml` needs `!override` — Compose *appends* to `ports`
  lists, so a plain remap still binds the original port and fails identically
- `BUZZ_HEALTH_PORT` 8080 conflict kills the relay *after* everything else reports
  healthy
- a mesh model costs **~2.6× its advertised size** (4.6 GB quoted → 12 GB on disk)
- disk exhaustion presents as a hang at `Resolving`, then a whole-session teardown
- `.window-state.json` can strand the dev window off-screen on a multi-monitor host
- relay verified: `/_liveness` → `ok`, WebSocket upgrade → `HTTP 101`

- **shared compute verified end to end**: toggle → 9337/3131 bound by
  `buzz-desktop` → `/v1/models` advertises the model → `/v1/chat/completions`
  returned `MESH_OK` (3 completion tokens). A *single* `heartbeat timed out` during
  startup is transient noise; the failure case emits it repeatedly and follows with
  `failed inference readiness`.
- `gemma-4-E4B` reports as **7.5B / 131k context** — the "E4B" label understates it

**Harness reply path verified in production (2026-08-18)** — a four-seat headless
deployment on a self-hosted relay, driven across `grok`, `claude-agent-acp`,
`codex-acp` and `agy-acp`. This supplies *The harness publishes nothing the agent
says* and *Engine choice decides whether a turn ever posts*: event kinds observed on
the relay, tool-call counts from `RUST_LOG=buzz_acp=trace`.

**Not verified by running:** the `deploy/compose` production bundle. Note that
a working `/v1/chat/completions` proves *serving only* — Buzz's own runbook is
explicit that it does not prove harness wiring or provider inheritance.

**Absence claims** (in *What Buzz does not have*) rest on repo-wide code search. Reproduce with:
```bash
for q in should_respond loop_guard consecutive_turns turn_limit; do
  echo -n "$q: "; gh search code --repo block/buzz "$q" --limit 5 --json path | jq length
done
```
All four returned **0 hits** again on 2026-08-05. `respond_to` and `mention`
(20 hits) were also searched — every `mention` hit was UI (autocomplete, chips,
highlighting, `hasMention.ts`) plus `crates/buzz-sdk/src/mentions.rs`; no server-side
reply decision.

**Not read:** `crates/buzz-agent/src/{agent,llm,config,mcp}.rs` (bodies), most relay
internals, desktop/mobile clients, and NIP bodies other than NIP-PMA. Absence claims rest on
targeted code search, so treat them as strong evidence rather than proof, and re-check
against a current checkout before relying on them.

Flags, defaults, and CLI surfaces drift. `--help` and the crate READMEs win over this
document.
