---
name: hermes-developer
description: "Develop Hermes Agent core, plugins, platform adapters, providers, tools, and skills using current Nous Research docs and code."
license: MIT
metadata:
  version: 1.3.26
  author: Mahdi Hedhli
  platforms: [linux, macos, windows]
  hermes:
    tags: [hermes, developer, architecture, contributing, plugins, tools, skills, providers]
    homepage: https://github.com/MahdiHedhli/skills/tree/main/skills/hermes-developer
    related_skills: [hermes-agent]
---

# Hermes Developer

Use this skill for Hermes implementation, extension, integration, and contribution work. For routine setup or use of an installed instance, consult the Hermes user docs or the `hermes-agent` skill if available.

This is a navigation aid, not a frozen API contract. Before substantive work, read the current [developer guide](https://hermes-agent.nousresearch.com/docs/developer-guide/), the target checkout's `AGENTS.md` and relevant area `AGENTS.md`, then verify the actual call path in source. Follow the target repository's instructions and the user's scope. A version-matched checkout is the authority for code that must run on that version; current upstream docs and code are the authority when the user asks for the latest Hermes. Record the commit used. Do not update an installed Hermes checkout or live home as a side effect of refreshing this skill.

## Design constraints

From current [Hermes AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md):

- Preserve the cached prompt prefix for a conversation. Changes to skills, tools, and memory normally take effect in a later session; a user-requested `--now` path may invalidate it explicitly. Context compression is the normal exception.
- Keep the core model tool schema small. Choose the least-footprint path that fits: extend existing code → CLI command plus skill → service-gated tool → plugin → MCP catalog → core tool. A surface available only to a particular client/session belongs in a session-selected toolset, not a process-wide `check_fn` or environment gate.
- Preserve strict message alternation and do not inject a synthetic user message into an active tool loop.
- Resolve profile-aware paths through `hermes_constants`, not a hardcoded `~/.hermes` path. Keep secrets in `.env` and behavior settings in `config.yaml`.
- Verify the observed bug and original design before changing a boundary. Third-party product integrations belong in standalone plugin repositories.
- The temporary Sep 2026 old-import compatibility layer has been removed. Internal import paths are not plugin APIs; use `ctx` and documented ABCs where possible, and resolve any remaining private import against the target build.

## Code map

| Concern | Start in code | Read |
|---|---|---|
| Agent turns | `run_agent.py` facade; `agent/conversation_loop.py`, `agent/turn_*.py` | [Agent loop](https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop) |
| Prompt and cache | `agent/prompt_builder.py`, `agent/system_prompt.py`, compression modules | [Prompt assembly](https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly), [caching](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching) |
| Tools | `tools/registry.py`, `model_tools.py`, `toolsets.py` | [Tools runtime](https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime) |
| Sessions | `hermes_state.py` facade and `hermes_state_*.py` siblings | [Session storage](https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage) |
| Gateway | `gateway/run.py` facade, `gateway/run_*.py`, `gateway/session*.py` | [Gateway internals](https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-internals), [session lifecycle](https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-session-lifecycle) |
| Plugins | `hermes_cli/plugins.py`, `gateway/platform_registry.py`, `plugins/` | [Plugin guide](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) |
| CLI | `cli.py`, `hermes_cli/commands.py`, `hermes_cli/cli_*_mixin.py` | [CLI internals](https://hermes-agent.nousresearch.com/docs/developer-guide/cli-internals) |
| Providers | `hermes_cli/runtime_provider.py`, `hermes_cli/auth.py`, `plugins/model-providers/` | [Provider runtime](https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime) |

Hermes uses facade modules with focused sibling modules. Trace the current facade export and owning sibling before editing. Do not assume a method still lives in the former large module. `AIAgent` serves CLI, gateway, ACP, batch, API server, and library callers; platform behavior belongs at their entry points. For full navigation, use [references/docs-index.md](references/docs-index.md) and [references/architecture-snapshot.md](references/architecture-snapshot.md).

## Choose the extension surface

- **Existing workflow:** a Hermes CLI command and skill, when possible.
- **Local or third-party capability:** native plugin under a user/project plugin directory, or a separately distributed package. The standard plugin has `plugin.yaml`, `__init__.py` with `register(ctx)`, and only the declared registrations it needs. `hermes plugins validate` and `hermes plugins list` help inspect discovery. Check the current [plugin manifest and dependency rules](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) before packaging; dependencies are managed by Hermes PM.
- **GitHub plugin distribution:** decide the install root before arranging the repository. On inspected Hermes `main` `39faafb6`, bare `owner/repo` clones and scans the whole repository; `owner/repo#subdir` selects a sparse subdirectory. Tests, docs, and CI beside a root plugin therefore affect the install scan. Keep findings visible and review them; see [extension map](references/extension-map.md).
- **Pinned plugin updates:** on Hermes `8afaab37`, `hermes plugins check-updates` does not compare a pinned plugin with newer releases, and `hermes plugins update <name>` refuses to advance its SHA. `hermes update` updates core and reports plugin compatibility concerns but does not update the plugin. A release checker should compare published tag commits by ancestry and treat compatibility-list matches as advisory. Keep explicit SHA updates and rollback, and verify compatibility after a core update; see [integration boundaries](references/integration-boundaries.md).
- **Messaging channel:** a platform plugin is the preferred route. Implement `BasePlatformAdapter`, register with `ctx.register_platform`, and follow [Adding Platform Adapters](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters) plus `gateway/platforms/AGENTS.md`. Bundled platforms are mostly in `plugins/platforms/`; `gateway/platforms/` also has shared and legacy adapters. `kind: platform` loading is deferred, so place outbound model tools in a separate declared `tools.py` if they must be available without starting the adapter.
- **Model, memory, context, media, search, browser, secret, or terminal environment backend:** read the matching typed-plugin guide before selecting an interface. The [plugin guide](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) routes among them. A language pack can declare `provides_locales` and ship `locales/<id>[.tui|.desktop].yaml` without Python registration.
- **Core model tool:** use only when the existing surfaces cannot provide the capability. Registration lives in `tools/*.py`; exposure is selected through `toolsets.py`. `check_fn` is for process-wide reachability or opt-in, not session/client identity. Verify the handler's current return and error contract in [Tools Runtime](https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime).

See [references/extension-map.md](references/extension-map.md) for the decision table. A plugin should not patch Hermes core files or assume a private internal is a stable plugin API. If an integration needs a missing primitive, identify the generic interface gap and check upstream plans before inventing a private workaround.

For mobile or other remote clients, distinguish a profile from a Bot Mode bot, keep model/config writes inside the routed profile's home and secret scope, and check whether an operation exists on the gateway adapter surface or only in Desktop's TUI RPC. See [integration boundaries](references/integration-boundaries.md) for verified examples and security traps.

For profile-scoped send routes, validate the target profile's own API server key and effective gate, not only the plugin-wide send flag. Preserve the client's draft until its encrypted pending-send record is durable, retain text after a definitive host refusal, and keep a pending outcome visible if the gate later closes. The exact-build behavior and source paths are in [integration boundaries](references/integration-boundaries.md).

Treat a read-only host setup check as a prerequisite check, not a per-bot send guarantee. Verify each served profile's route, secret scope, and authorization separately before enabling writes. A newly created profile can be served yet lack its exact root `hmp` route (`not_routed`); verify the build's matcher and see [integration boundaries](references/integration-boundaries.md).

When a paired device can perform persistent host actions such as scheduling jobs or changing a bot's default model, require a separate per-device host decision. Pairing and Bot Chat grants do not imply this privilege, even when devices share a user. Default new devices to denied, make the host prompt unambiguous so an earlier yes/no answer cannot grant controls, and provide an explicit host-only way to revoke the decision. Test the denial and grant at the actual route gate; see [integration boundaries](references/integration-boundaries.md).

For pairing failures, distinguish an unreachable host from a received error on an instance-pinned connection. A connection failure does not prove that Tailscale is down; a 5xx does not prove the offer is bad or that a P4 activation did not occur. Suggest a fresh offer only for an identified code or offer problem, and do not automatically retry an uncertain P4 result. See [integration boundaries](references/integration-boundaries.md).

For a phone's QR-derived host precheck, verify the QR identity on the TLS connection before a diagnostic `GET /hmp/v1/ready`. Send no key, offer secret, or authorization material before fingerprint confirmation. A 200 proves only that this pinned route answered then; it cannot authorize pairing or attest a bot channel. The first pairing-pool pin check now happens before key generation, so adjust acceptance fixtures accordingly; see [integration boundaries](references/integration-boundaries.md).

For multi-profile plugins, derive operator health from the running gateway's
served set, effective feature flags, exact-build gates, and each profile's
scoped endpoint. Keep snapshots fresh, bounded, and status-only; fail closed
on stale or incomplete data. Route health does not prove device authorization
or a later turn's outcome.

When replacing a live platform plugin, check the gateway's active-work status
before a drain-aware restart. An install into an isolated `HERMES_HOME` should
use an isolated Hermes build: an installed source checkout's CLI bootstrap may
first finish its own dependency or product update, even when the target home is
temporary. `plugins doctor` can warn about missing declared dependencies while
the plugin is disabled; enable it, then check again. A plugin reload may leave
an old adapter's runtime health snapshot in place until the gateway restarts.
Confirm the exact installed commit, Plugin Doctor, compatibility, and fresh
per-profile health after restart; verify one real client send separately.

For gateway platform messages, distinguish task scheduling from durable admission. On the inspected experimental Hermes build, `_gateway_accepted` can be true before the later `AdmissionTicket` outcome. Wait for `admission_ticket.reported` where that API exists; treat `refused_other` as ambiguous when its reason is unavailable, since it can include `persist_failed`. Keep missing, unfamiliar, or timed-out outcomes under the same idempotency key without automatic retry, and add a local transcript observation only after confirmed admission. The older inspected stock-base `04fa849e` and experimental `7e8c8f07` session-chat streams lacked the approval notifier used by `/v1/runs`; untagged main `ac0cfa7` registered it and passed an isolated HMP real-gateway fixture, though no released build is qualified. Check the exact route and build before promising answerable Bot Chat prompts; see [integration boundaries](references/integration-boundaries.md#search-and-approval-privacy).

For a mobile session picker or any check-then-read of a current session's messages, `SessionDB.get_session` and `get_messages` on `8afaab37` use separate read contexts, so an eligibility check followed by a read can race a fork or lineage change. Prefer an upstream transactional primitive over copied SQLite logic; see [session snapshot gap](references/integration-boundaries.md#session-snapshot-consistency).

## Development and verification

Current Hermes development uses its package manager (PM), not the older `uv pip install -e` recipe. For a checkout you are authorized to prepare, choose isolated `HERMES_HOME` and `HERMES_RUNTIME_DIR`, then follow [PM developer workflow](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow) and `source ./activate` (PowerShell: `. .\activate.ps1`). Current development uses PM's pinned Python 3.14; package metadata supporting older Python does not mean the current development environment uses it.

For an exact-build plugin compatibility check, choose the interpreter from that Hermes revision's lock and test workflow. Do not assume a fixture extractor's hardcoded Python version is suitable. Bind a git install to both its reviewed source fingerprint and commit SHA; verify packaged wheels contain the compatibility data they read. See [integration boundaries](references/integration-boundaries.md).

For tests, build an independent interpreter from the committed lock if needed:

```bash
python -m pm.build_env --source . --out .venv --group dev --group test
scripts/run_tests.sh tests/gateway/ -v
```

The destination must be fresh. `scripts/run_tests.sh` is the required runner for Hermes core tests; it isolates credentials, homes, locale, and test files. Use real imports and a temporary `HERMES_HOME` for config, profile, network, and security boundaries. For profile-scoped changes, verify A→B→A. Never aim tests at a live Hermes home. Dependency changes use PM and the lockfile; observe current upper-bound and pinning rules in `AGENTS.md`. See [references/contributing-checklist.md](references/contributing-checklist.md).

## Refresh this skill

The installed snapshot was checked against NousResearch/hermes-agent `81f481b2db39e9c3e3df8cbb063931746263eca2` on 2026-09-28. Refresh before a substantial Hermes task when the target or upstream has moved:

1. Compare the target checkout with current [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), its root and area `AGENTS.md`, and the relevant developer pages. Use an isolated checkout for a latest-upstream comparison; do not pull a user's installed Hermes without authorization.
2. Set `HERMES_AGENT_REPO` to that checkout and run `python3 <this skill>/scripts/refresh_from_docs.py`. It discovers every developer-guide Markdown page recursively and writes `references/LAST_REFRESH.md` plus the heading snapshot. It does not rewrite this entrypoint.
3. Read changed pages and the corresponding code. Update this file and only the affected references. Resolve disagreements by verifying the current code path and noting the version boundary; do not silently turn one version's behavior into a universal rule.
4. Validate with the skill creator's `quick_validate.py` when available. Check links and at least one important code claim against source.

Detailed page routing: [docs index](references/docs-index.md). Latest refresh metadata: [LAST_REFRESH.md](references/LAST_REFRESH.md).
