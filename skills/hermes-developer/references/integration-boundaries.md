# Remote-client integration boundaries

Verified against NousResearch/hermes-agent `81f481b2db39e9c3e3df8cbb063931746263eca2` (2026-09-28). These are code-path observations for extension authors, not promised plugin APIs. Recheck the version a client actually runs.

## Bot lifecycle

A Hermes profile is the bot's persistent home, but creating a profile alone does not complete the Bot Mode lifecycle. The [Bot Mode guide](https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode) and [Profiles guide](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) describe roster presentation and the canonical Bot Chat. Desktop's flow uses `profiles.create`, stores presentation metadata, then calls `session.create` and `session.title` for the hidden `Bot Chat` (`apps/desktop/src/plugins/hermes-bots/create-dialog.tsx`, `canonical-chat.ts`). The session is lazy until title or first activity persists it; the title can race another creator, so Desktop adopts the existing winner. `tui_gateway/methods_session.py` owns those RPCs. A gateway platform plugin should not assume it can call them in-process, or equate a newly created profile with a usable canonical chat.

The profile-scoped API server has `GET /api/sessions?title=Bot Chat&include_hidden=1` and `POST /api/sessions` with a title; the latter does not atomically apply hidden and profile-following state. `hermes peer dm` uses the lookup/create pair and treats a title conflict as a possible hidden existing chat. Do not equate these lower-level routes with an idempotent Bot Mode create-or-get contract. The API server does not expose profile create/delete; those live in Desktop's TUI gateway/dashboard and the profile CLI. Check all of creation, canonical-chat identity, and partial-failure recovery before adding a remote bot lifecycle UI.

`hermes_cli/profiles.py::delete_profile` removes the profile's config, memories, sessions, and skills, may stop profile backends, and can report that identity settlement is still pending after the directory is gone. The default profile is protected. A remote delete surface needs exact profile identity, owner authorization, an explicit destructive confirmation, and a result that distinguishes complete deletion from settlement pending. Treat a lost delete response as uncertain; read state before offering another attempt. Do not expose a generic shell or profile-path argument to the client.

The API server already provides session list/read, metadata PATCH, DELETE, and `/fork` on a profile. `/fork` ends the source session; it is not a non-destructive branch. Keep canonical Bot Chat deletion/archive outside a generic remote session-management UI, and treat project move/export/open-in-terminal as separate capabilities to verify rather than inferring them from the existing session routes.

## Exact-build plugin qualification

HMP's compatibility gates cover selected Hermes source files. For a git
installation, require both the reviewed file fingerprint and exact commit
SHA. A read-only source archive can prove its bytes match a clean checkout,
but it has no git identity; do not add a fingerprint-only archive entry just
because the git checkout passed. Run Hermes tests through
`scripts/run_tests.sh` and plugin integration against temporary homes.

The HMP fixture extractor pinned Python 3.11, while Hermes `8afaab37` needed
Python 3.14 for its locked dependencies. Select the interpreter from the
target build's package workflow and keep generated environments outside the
live Hermes home. Build the plugin wheel and inspect its contents when a
runtime gate reads package data; source-tree tests can miss an omitted JSON
allowlist or manifest.

## Gateway setup and profile routing

On Hermes `8afaab3703`, `hermes_cli/config_defaults.py` advertises
`gateway.multiplex_profiles: true`, but `gateway/config.py` preserves an unset
raw value as `None`. At gateway startup,
`hermes_cli/gateway_multiplex_mode.py::resolve_multiplex_mode` runs a blocker
preflight for unset or retired `false` values; an explicit `true` takes its
direct config path. Do not interpret `hermes config get`'s resolved default as
proof that multiplexing is active, or automatically write `true` to make a
plugin work. On a multi-profile host, review
`hermes gateway migrate --multiplex --dry-run` and the actual gateway state.
Explicitly enabling multiplexing can make `/p/<profile>/` reachable on the
default API listener and change secret scoping. Treat those as host-wide
security decisions, not a mobile plugin's routine setup step.

HMP's older fixture-qualified builds also require `gateway.profile_routes`
entries for the `hmp` platform and used explicit multiplex settings in root
and served-profile config. Requalify that configuration shape against the
exact Hermes build before a setup wizard edits it. A plugin should report a
missing route or unserved profile explicitly rather than forcing topology or
opening another host surface.

On Hermes `8afaab37`, `gateway.run::_profile_runtime_scope` binds each named
profile's secret mapping. `gateway.platforms._shared::get_scoped_secret`
does not fall back to the root process environment when a named profile's
`API_SERVER_KEY` is missing. HMP's guarded direct-send endpoint therefore
fails closed for that profile even if the plugin-wide `direct_send.enabled`
flag is true. An instance-wide roster gate based only on that flag does not
prove each bot's endpoint resolved. In a multi-profile plugin, report a
per-bot send gate from the same profile-scoped prerequisites as the route;
keep an older aggregate gate conservative and treat malformed client-side
status as closed. A full Hermes write guarantee must not bypass a separate
owner switch on a plugin route that still uses the keyed loopback endpoint.
The route rechecks at submission, and a failed draft stays recoverable. Check
the target profile's own key source without logging the key or copying
another profile's credential. This HMP correction is draft PR #7, not a
claim about the installed plugin until it is merged and deployed.

## Emerging unified gateway

As of 2026-09-28, NousResearch/hermes-agent
[#106742](https://github.com/NousResearch/hermes-agent/pull/106742) is an
open, unmerged proposal for one profile-scoped `SessionAuthority` owning
durable admissions, FIFO execution, shared controls, and recovery. The
companion [entry-point plan](https://gist.github.com/unsupportedpastels/765f9d551ce88ee01630c18367763e75)
explicitly places a future mobile client behind an authenticated gateway API,
but treats remote `serve`/Desktop/web cutover as later work. Do not import the
proposed authority classes or assume their wire shapes exist in an older
installed Hermes. A mobile plugin must remain a reader/submitter of the
qualified host and must not become another execution owner.

HMP's current phone reserves a `client_message_id`, represents ambiguous
sends as unconfirmed, and resnapshots after a history reset. A pending-send
storage write must be a hard gate before clearing the draft or transmitting;
best-effort persistence can leave a refused send with no visible text. A
definitive `write_gate_closed` response must retain the unsent text for review,
even if a refreshed roster becomes read-only. These safeguards are reusable;
a mailbox `queued` response is
not a canonical authority admission, and a snapshot reset is not event replay.
Prefer narrow capability/identity seams and acceptance fixtures now. Build a
versioned remote adapter only after the target Hermes release exposes a
supported authenticated entry, then verify shared session identity, exact
retry, unknown work, replay/snapshot recovery, and stale-control fencing.

## Profile model and credentials

`hermes_cli/web_routers/profiles.py::_write_profile_model` validates a provider/model choice and writes under the selected profile's config and secret scope; it is an internal helper. `hermes_cli/inventory.py::build_model_options_payload` backs `GET /api/model/options`, including authenticated choices. A custom provider's picker row can use the bare slug while persisted config reports `custom:<slug>`; use its aliases or normalize deliberately when showing the selected row. Keep credentials, endpoint URLs, and raw config out of a remote picker response. Gate internal writer use to a qualified build and test profile A → B → A, including which profile's credential validates each write. Do not replace Hermes's validation with a client-side allowlist.

## Search and approval privacy

`hermes_state_search.py::search_messages` currently logs the raw search query on a slow call (`query=%r`, up to 200 characters). A remote search UI can therefore place private user text into host logs even if the plugin never logs it. Check the target build's logging path before exposing search; an upstream fix or a reviewed, version-qualified mitigation is needed.

Approval and clarify waits use Hermes's own profile-scoped timeouts: `approvals.timeout` (default 300 seconds) and `agent.clarify_timeout` (default 3600 seconds). A client-side timer does not own the pending decision; `api_server_runs.py` can return `409 approval_not_pending` for a late answer. Bind a remote answer to the authorized device and exact pending request, deny access to gateway control paths, bound observation resources, and avoid logging answer text. An approval integration must observe Hermes's pending state rather than infer it from elapsed time alone.

On extracted stock-base `04fa849e` and experimental `7e8c8f07`, the session-chat stream does not register an approval notifier or emit `approval.request`; the `/v1/runs` path has a separate notifier and cannot silently replace a guarded Bot Chat send. HMP's mandatory real-route approval fixture fails on both builds. The experimental `BasePlatformAdapter.handle_message` sets `event._gateway_accepted` when it spawns background processing, before durable admission or refusal is reported through `MessageEvent.admission_ticket` for `defer_policy="reject"`. Returning `202 submitted` from that flag alone can misstate a later refusal. Draft HMP PR #8 now waits for the ticket: only `admitted` reports submitted, `refused_*` reports refusal, and an absent or timed-out result is stored as `unknown` under the original cmid so a replay does not send again. Stock-base lacks the ticket API and keeps its synchronous acceptance behavior. For fixture sends after a gateway restart, wait until Hermes releases its startup-restore gate; an open listener and populated bot roster are too early, and the experimental build correctly reports `refused_draining` then. The isolated T8 Phone chat fixtures now pass on both exact builds, but full qualification still fails on mandatory T7. Keep approvals disabled until that upstream gap is resolved and a full fixture run passes.
