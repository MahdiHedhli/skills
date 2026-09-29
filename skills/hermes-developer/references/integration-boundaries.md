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

HMP's draft `hermes hmp setup check` is deliberately read-only. It checks the
qualified build, plugin instance, identity, and listener, but it does not
validate each served profile's route, `API_SERVER_KEY`, or owner authorization.
Its success cannot certify a particular bot's send path. Pair it with a
profile-scoped capability check and a real-route fixture before enabling
writes; do not change host topology or copy a root secret as an automatic
repair. This HMP setup check is in draft PR #10 until merged and deployed.

Draft HMP PR #11 adds a separate `hermes hmp health check`. The running
adapter refreshes a status-only snapshot for each served bot using live
feature flags, exact-build qualification, and profile-scoped endpoint lookup.
The CLI checks the same TLS-pinned listener and rejects stale, missing, or
incomplete snapshots. Intentionally disabled channels differ from enabled
channels whose route or key is unavailable. No key or endpoint belongs in a
diagnostic record. The check cannot certify a device's bot access or a later
request outcome.

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

A client roster refresh can close a bot's gate after a send begins. Render the
pending outcome before the generic read-only state: keep an unconfirmed result
available for read-only status lookup, keep a definitive refusal's text
reviewable, and withhold retry or new-send actions while the gate is closed.
This is a client-state lesson from draft app PR #16, not a new Hermes API claim.

For an explicit "Send as new" after an ambiguous or failed Bot Chat send,
reconcile the old `client_message_id` through a read-only status lookup first.
Accepted or queued means no replacement POST; submitted remains pending.
Before a new attempt, refresh that bot's authorization and write gate and
read a canonical chat snapshot for its current head. Serialize this action
with status check and discard, and atomically replace the encrypted pending
record with the new ID and text before transmitting. Clearing the old record
first can lose the only recoverable draft if a read or storage write fails.
A failed preflight leaves the old record visible; a foreground switch stops
the new POST. This is a mobile client recovery lesson, not a new Hermes API.

A guarded send may report `submitted` after a short admission wait while
Hermes continues a long turn. The phone may observe transcript rows during
same-id status reconciliation. Keep pending text encrypted and visible, label
the wait as delivery checking, and never settle it solely because matching
transcript text appears. Draft app PR #20 also keeps a long transcript pinned
to its latest row after late layout growth unless the reader scrolls up.

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

## Per-device privilege after pairing

HMP's owner-controls draft at `3c32796` separates pairing and Bot Chat access from persistent job and default-model writes. The host must type the full word `GRANT` for the specific device after pairing; every other answer records a denial. A durable per-device decision takes precedence over the older configuration allowlist. New device IDs do not inherit a shared user's privilege, and a revoked device cannot be granted controls. The CLI can grant or deny later under its host-terminal guard. The gateway still checks an active device token and profile authorization on each request. Exercise both job and model routes with explicit denial overriding legacy configuration, then with an explicit grant and no legacy entry. This draft needs security review before release; it is an integration pattern, not an upstream Hermes API.

Real-PTY pairing fixtures must handle the separate post-confirmation host
prompt. A helper that launches `hermes hmp pair confirm` and only waits for
process exit now times out there. For ordinary read/send fixtures, wait until
the prompt appears and submit an empty answer so controls remain denied;
privilege fixtures should answer `GRANT` only in the cases testing that grant.
Do not prefill the terminal with a yes/no response that could be consumed by
the wrong prompt. The combined HMP stock-base and experimental direct-send
fixtures passed after this helper correction.

Qualify persistent-control routes separately on each build. In the isolated
HMP two-device gateway fixture, the experimental Hermes revision retained the
qualified cron bridge fingerprint but not the model bridge fingerprint: the
host-granted phone could create a paused job, while model management still
returned unavailable. The ungranted sibling saw neither route. A device grant
must never override a feature's exact-build gate.

## Mobile cron delivery and continuity on Hermes `8afaab37`

The profile-scoped `/api/jobs` route accepts `deliver` and `repeat` but not
`continuity` or `context_from`. A job created with `deliver: local` can run
successfully without posting to a Bot Chat; show the destination and last run
status before diagnosing it as a failed scheduler. Desktop's “Run history only”
maps to `local`, and “Hermes's chat (bot responds)” maps to the bare `bot-chat`
token in the selected profile. Desktop continuity maps to `context_from` with
`self`. For a plugin needing that setting in the same write, call the exact
qualified `cron.scheduler.create_job_with_scheduler_registration` and
`cron.jobs.update_job` under `gateway.run._profile_runtime_scope`, applying the
same prompt scan and lifecycle guard as Hermes's HTTP route. Keep arbitrary
delivery targets and raw cron records out of a phone facade; preserve other
context references when toggling `self`. An isolated-home check on both the
installed source and extracted stock build verified paused creation, delivery,
continuity, finite runs, and edit. This is a version-specific private bridge,
not a stable plugin API.

## Pairing failure guidance

The HMP mobile client's F19 pairing-error change distinguishes transport
failure from a received 5xx on the pinned connection. The former can suggest
checking Tailscale and host reachability, but it cannot diagnose which one is
down. A received 5xx points to a host problem even if its error body is
malformed; a recognized exact-build refusal still deserves its specific
message. Limit "ask for a new pairing code" to identified code or offer
problems. It is misleading after a pin mismatch, failed response verification,
or an internal host error.

A P4 5xx can occur after Hermes has handled activation. The phone may discard
its unusable new key without knowing whether a host device record was created.
Do not claim no activation, automatically re-send P4, or treat the result as a
routine expired offer. Exercise both a 5xx returned before handling and one
substituted after host handling in a pinned fake-server test. Keep error body,
endpoint, code, and device identifiers out of user-visible diagnostics and
normal logs. This is a client-side integration lesson, not a new Hermes API.

HMP mobile F21 adds an optional pre-S2 check after a valid QR supplies the
endpoint and instance pin. Open the connection with that QR pin before sending
an unauthenticated `GET /hmp/v1/ready`; send no device key, offer identifier,
offer secret, or authorization header. Treat the response body as diagnostic,
not an identity or capability grant. A 200 only proves that route answered at
that moment, so P2/P4 and the user's fingerprint confirmation remain required.
Cancel or a newer scan must close the pool and suppress late results. The host
can observe the phone's source address and timing as soon as it scans, so make
the check visible and cancellable. In the acceptance matrix, a wrong-key
first pairing connection now fails on this readiness request before hardware
key generation; update the expected step without weakening the pin assertion.
Use a scripted pool for unit tests: a synthetic CGNAT endpoint is not a safe
network target merely because the offer is synthetic.

## Profile model and credentials

`hermes_cli/web_routers/profiles.py::_write_profile_model` validates a provider/model choice and writes under the selected profile's config and secret scope; it is an internal helper. `hermes_cli/inventory.py::build_model_options_payload` backs `GET /api/model/options`, including authenticated choices. A custom provider's picker row can use the bare slug while persisted config reports `custom:<slug>`; use its aliases or normalize deliberately when showing the selected row. Keep credentials, endpoint URLs, and raw config out of a remote picker response. Gate internal writer use to a qualified build and test profile A → B → A, including which profile's credential validates each write. Do not replace Hermes's validation with a client-side allowlist.

## Search and approval privacy

`hermes_state_search.py::search_messages` currently logs the raw search query on a slow call (`query=%r`, up to 200 characters). A remote search UI can therefore place private user text into host logs even if the plugin never logs it. Check the target build's logging path before exposing search; an upstream fix or a reviewed, version-qualified mitigation is needed.

For a narrower phone-only search, HMP can expose authorized Bot Chat history pages and let the phone match text locally, without sending a query to Hermes. Do not conflate the old mobile-only RO-6 `after=0` branch with the canonical Bot Chat: SES-2 `after=0` returns a **latest** snapshot. HMP draft PR #13 adds a distinct `messages/from-start` route for the earliest active canonical rows; continue with SES-2 `after=<last id>` toward the first page's frozen head. Apply the existing per-bot gate and opaque session ref, then bound reads and results, fail visibly on reset/empty-page anomalies/limits, and discard results after an active-instance switch. Hermes compaction can remove earlier rows, so describe this as search over available Bot Chat history, not all Hermes history or all time.

Approval and clarify waits use Hermes's own profile-scoped timeouts: `approvals.timeout` (default 300 seconds) and `agent.clarify_timeout` (default 3600 seconds). A client-side timer does not own the pending decision; `api_server_runs.py` can return `409 approval_not_pending` for a late answer. Bind a remote answer to the authorized device and exact pending request, deny access to gateway control paths, bound observation resources, and avoid logging answer text. An approval integration must observe Hermes's pending state rather than infer it from elapsed time alone.

On extracted stock-base `04fa849e` and experimental `7e8c8f07`, the session-chat stream does not register an approval notifier or emit `approval.request`; the `/v1/runs` path has a separate notifier and cannot silently replace a guarded Bot Chat send. HMP's mandatory real-route approval fixture fails on both builds. The experimental `BasePlatformAdapter.handle_message` sets `event._gateway_accepted` when it spawns background processing, before durable admission or refusal is reported through `MessageEvent.admission_ticket` for `defer_policy="reject"`. Returning `202 submitted` from that flag alone can misstate a later refusal. Draft HMP PR #8 now waits for the ticket: only `admitted` reports submitted; known specific refusals report failure; `refused_other`, unfamiliar, absent, and timed-out outcomes remain `unknown` under the original cmid so replay does not send again. `refused_other` can represent `persist_failed`, and the ticket does not expose its reason, so it must not be treated as a definitive failure. Add a Phone chat transcript observation only after confirmed admission; otherwise a refused turn can appear delivered. Stock-base lacks the ticket API and keeps its synchronous acceptance behavior. For fixture sends after a gateway restart, wait until Hermes releases its startup-restore gate; an open listener and populated bot roster are too early, and the experimental build correctly reports `refused_draining` then. The isolated T8 Phone chat fixtures now pass on both exact builds, but full qualification still fails on mandatory T7. Keep approvals disabled until that upstream gap is resolved and a full fixture run passes.
