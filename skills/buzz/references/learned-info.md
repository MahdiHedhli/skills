# Buzz learned info

This is the skill's durable learning channel. It stores evidence-backed discoveries
that may be useful across sessions, including operational observations that are too
new or narrow for the canonical guidance.

## Rules

- Search this file before investigating a matching symptom or subsystem.
- Record reusable facts, not a transcript of the task that exposed them.
- Include a source and concrete evidence. Label inference honestly.
- Never record secrets, private keys, access tokens, personal data, or private relay
  content.
- Keep entries after promotion or rejection so the evidence trail remains intact.
- Promote a verified fact into `SKILL.md` or the expert reference when it changes
  canonical guidance, then set the entry status to `promoted` and name the target.

## Entries

<!-- Append records below with scripts/record_learning.py. -->

<!-- buzz-learning:589f0faa256c -->
### 2026-08-05 — Owner-only includes verified sibling agents

- ID: `589f0faa256c`
- Area: harness
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@16cc3de6d6bb:crates/buzz-acp/src/lib.rs; block/buzz@16cc3de6d6bb:desktop/src-tauri/src/managed_agents/access_policy.rs
- Evidence: Read author_allowed, is_owner_or_sibling, DM fail-closed resolution, and Desktop policy comments.
- Finding: The default owner-only gate accepts the human owner and NIP-OA-verified agents with the same owner; DMs restrict all responding modes except nobody to that trust domain, so sibling A-to-B loops remain possible.
- Canonical target: The dispatch model; Debugging; comparison

<!-- buzz-learning:3812f3f6d351 -->
### 2026-08-05 — Kind 30179 is reserved but inert

- ID: `3812f3f6d351`
- Area: protocol
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@067c085f37d9:docs/nips/NIP-PMA.md; block/buzz@067c085f37d9:crates/buzz-core/src/kind.rs
- Evidence: Read the NIP status and deployment order, kind registration, author-only classification, and relay rejection test.
- Finding: NIP-PMA kind 30179 defines an owner-self-encrypted private managed-agent aggregate, but generic relay ingest must reject it until privacy, transactional CAS, revocation, and capability gates deploy.
- Canonical target: Event kinds

<!-- buzz-learning:d3559e0d5658 -->
### 2026-08-05 — Multi-repo projects do not confer repository authority

- ID: `d3559e0d5658`
- Area: git
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@cb9701cd30fb:crates/buzz-core/src/kind.rs; block/buzz@b7bb15122e8a:crates/buzz-cli/src/lib.rs
- Evidence: Read the kind contract and all seven buzz projects command definitions.
- Finding: Kind 30621 groups kind:30617 repository coordinates, including cross-owner repos; project membership and its optional channel link do not change each repository announcement’s push policy.
- Canonical target: Git; Event kinds; Agent-facing surfaces

<!-- buzz-learning:33c859b46448 -->
### 2026-08-05 — Buzz entities return canonical deep links

- ID: `33c859b46448`
- Area: cli
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@a1d78f2959b4:crates/buzz-acp/src/base_prompt.md
- Evidence: Read current base prompt and exact entity-links commit diff.
- Finding: Repo creation, issue creation, and PR opening return a buzz:// link for in-app previews; agents should share it verbatim and not invent HTTPS URLs for Buzz-hosted repositories.
- Canonical target: Agent-facing surfaces

<!-- buzz-learning:bfcd3d0b49dc -->
### 2026-08-05 — Kubernetes sidecar and release mesh policy

- ID: `bfcd3d0b49dc`
- Area: desktop
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@a7ea86cdcf2a:desktop/src-tauri/tauri.conf.json; block/buzz@6530b58a61d4:desktop/src-tauri/tauri.windows.conf.json; block/buzz@16cc3de6d6bb:Justfile
- Evidence: Read current externalBin lists and desktop-release-build --features mesh-llm recipe; reconciled the historical artifact observation.
- Finding: macOS/Linux Desktop bundles buzz-backend-kubernetes while Windows excludes it; no package contains the relay. The current release recipe compiles mesh-llm even though a previously tested artifact lacked it.
- Canonical target: Running it; Provenance

<!-- buzz-learning:75a2ab4f3d5c -->
### 2026-08-18 — The harness publishes no agent text; agents speak only via the CLI

- ID: `75a2ab4f3d5c`
- Area: harness
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@50a71137e6f1:crates/buzz-acp/src/acp.rs; block/buzz@50a71137e6f1:crates/buzz-acp/src/pool.rs; block/buzz@54f11219efe6:crates/buzz-acp/src/relay.rs; crates/buzz-acp/src/base_prompt.md
- Evidence: Read acp.rs:144/1753 (turn_emitted_text is a flag with no publish path), relay.rs:855 build_typing_event, pool.rs:3883/3931 reaction add and build_remove_reaction, pool.rs:3681 publish_agent_turn_metric; grepped every Kind::Custom(9) site and confirmed all are in test modules.
- Finding: buzz-acp never turns agent output into a channel message. agent_message_chunk is consumed only to set the turn_emitted_text flag, and every Kind::Custom(9) construction in the crate is a test fixture. The harness publishes on its own behalf only the ephemeral typing indicator (20002), the ack reaction and its NIP-09 removal (7 then 5), and turn metrics (44200). An agent becomes visible only by executing 'buzz messages send'. base_prompt.md states this requirement once, mid-list.
- Canonical target: Agent-facing surfaces; Debugging

<!-- buzz-learning:7d6a8f660ccf -->
### 2026-08-18 — Engine choice decides whether a turn ever posts

- ID: `7d6a8f660ccf`
- Area: harness
- Status: promoted
- Confidence: observed
- Source: Reproduced on a four-seat headless buzz-acp deployment, 2026-08-18; RUST_LOG=buzz_acp=trace session/prompt traces
- Evidence: Compared tool-call counts per turn across engines on one job; channel showed ack reaction, typing indicator, kind-5 reaction removal and no kind 9 for every codex turn; direct ACP drive of codex-acp with an explicit shell instruction returned tool_call plus tool_call_update in both a trusted and an untrusted cwd.
- Finding: Swapping BUZZ_ACP_AGENT_COMMAND is not like-for-like. Because posting requires a tool call, an engine that answers conversationally completes the turn with stopReason end_turn and outcome ok while publishing nothing. Observed on one seat with identical brief, channel and working directory: grok 1.0.5 and claude-agent-acp 0.69.0 made 28 tool calls and posted; codex-acp 1.4.0 (codex-cli 0.147.0) made 0 and posted nothing. It is not a capability or sandbox-trust limit — the same codex build made tool calls in both trusted and untrusted working directories when told explicitly to run a command, and restating the posting requirement imperatively at the top of the seat's own AGENTS.md/CLAUDE.md moved it from 0 tool calls to 16 on the same prompt shape. Put the posting mechanism in the seat brief, not only in the base prompt.
- Canonical target: Running it (Full harness config); Debugging

<!-- buzz-learning:5aee048c6719 -->
### 2026-08-18 — codex-acp ignores config.toml sandbox_mode and defaults to networkAccess false

- ID: `5aee048c6719`
- Area: harness
- Status: promoted
- Confidence: source-verified
- Source: @agentclientprotocol/codex-acp@1.4.0 dist/index.js (AgentMode, getInitialAgentMode)
- Evidence: Read the AgentMode class definitions and getInitialAgentMode; confirmed the literal sandbox_mode never appears in the bundle. Reproduced the send failing with both error strings, then succeeding with accepted:true and exit_code 0 once INITIAL_AGENT_MODE=agent-full-access was set.
- Finding: codex-acp defines its own ACP agent modes in dist/index.js and never reads sandbox_mode from ~/.codex/config.toml. DEFAULT_AGENT_MODE is 'agent' with {type:workspaceWrite, networkAccess:false}, so any tool call that opens a socket fails — first as 'Temporary failure in name resolution', then as 'tcp open error: Operation not permitted (os error 1)' once the name resolves from /etc/hosts. Project trust_level does not affect it. AgentMode.getInitialAgentMode() reads the INITIAL_AGENT_MODE environment variable and falls back to that default, so INITIAL_AGENT_MODE=agent-full-access is the fix; it is inert for other runtimes. Separately, codex reads AGENTS.md and not CLAUDE.md, so a brief under the wrong filename is invisible to it. Both failures end the turn outcome=ok having posted nothing.
- Canonical target: Engine choice decides whether a turn ever posts

<!-- buzz-learning:db5f76d8649b -->
### 2026-08-18 — A codex seat cannot report its own inability to fork

- ID: `db5f76d8649b`
- Area: harness
- Status: promoted
- Confidence: observed
- Source: systemd unit drop-in TasksMax=512 on a codex-backed buzz-acp seat; codex-acp 1.4.0
- Evidence: A seat at TasksMax=64 produced zero tool calls and no post across many turns while an SSH-spawned driver with identical cwd, brief and env posted successfully. The turn's discarded assistant text read 'Unable to publish the reply: this turn's command runner failed to spawn'. Raising TasksMax to 512 and restarting produced a tool call and a kind 9 within 10 seconds on the next message.
- Finding: Under systemd, a conservative TasksMax on the agent unit is the dominant cause of a silent codex seat. The codex stack (codex-acp, codex CLI, git, bwrap) exhausts the pids cgroup at TasksMax=64; every fork then fails with EAGAIN and codex reports 'command runner failed to spawn'. Because agents post by forking the buzz CLI, the seat cannot publish the message explaining the failure: the turn ends outcome=ok, nothing is posted, and the harness logs no error. 512 is sufficient. Two diagnostics generalize: the discarded agent_message_chunk text contains codex's own accurate self-diagnosis, so read it before theorizing; and a standalone ACP driver spawned over SSH runs outside the service cgroup and will pass every time while the service keeps failing, so resource-limit faults must be reproduced inside the unit.
- Canonical target: Engine choice decides whether a turn ever posts

<!-- buzz-learning:737e79f76461 -->
### 2026-08-18 — BUZZ_ACP_PERMISSION_MODE default changed from dont-ask to bypass-permissions

- ID: `737e79f76461`
- Area: harness
- Status: promoted
- Confidence: source-verified
- Source: block/buzz@main:crates/buzz-acp/src/config.rs (PermissionMode, CliArgs::permission_mode)
- Evidence: Read the exact diff from pin ad538bfb1e6b to main: default_value changed from dont-ask to bypass-permissions, Auto and BypassPermissions variants added with as_wire_str entries. Also added: BUZZ_ACP_EFFORT_LEVEL and BUZZ_ACP_IDLE_POOL_SLEEP.
- Finding: On 2026-08-18 the buzz-acp permission-mode default flipped from dont-ask (reject anything needing interactive approval, because Buzz exposes no human prompt) to bypass-permissions (skip the per-tool-call permission flow entirely). An unchanged deployment therefore performs operations it previously refused. Two new modes exist: auto, which is model-gated on supportsAutoMode and degrades to default, and bypassPermissions. Set BUZZ_ACP_PERMISSION_MODE=default to restore built-in prompting. The mode is delivered via session/set_config_option with configId 'mode', which matches claude-agent-acp; codex-acp uses the same configId with disjoint values (agent, agent-full-access, read-only), so Buzz permission-mode strings are meaningless to it.
- Canonical target: Running it (Full harness config); The permission model
