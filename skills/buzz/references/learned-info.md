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
