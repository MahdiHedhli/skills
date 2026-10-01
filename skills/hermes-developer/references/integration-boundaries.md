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

Verified 2026-09-30 on Hermes `ca705dbf7ef86425b381b542712aff310f1ee52c`: a
live gateway served a newly created profile while root
`gateway.profile_routes` had no exact `hmp` route for it. Gateway profile
reconcile rescans the served profiles but does not update the running root
runner's HMP routes, so HMP's source builder correctly returned `not_routed`.
Serving, authorization, and a successful send are separate facts. Compare
`gateway/run_profile_reconcile.py`'s served-profile reconciliation with
`gateway/run_adapters.py`'s routing and the matcher in `gateway/config.py`;
check the target build's actual matcher and version before repairing.

On that exact `ca705dbf` build, the multiplexing root already discovers and
serves eligible named profiles; their own `multiplex_profiles` flag is not a
serving prerequisite. Do not change a profile's own flag as a route repair:
it affects the session namespace and can make existing history inaccessible.
Prepare only an exact root HMP route for the intended profile, preserving its
config and history. Root routes remain loaded in the running gateway's config;
profile rescan and plugin handler reload do not hot-refresh that table, while
SIGUSR1 performs a drain and restart. Automatic new-bot enrollment needs a
qualified route-activation primitive rather than merely a config write.
HMP PR #52 at `4e270f0` corrects that profile-flag write: only the exact root
route is written. Root and focused review cleared the configuration-write
candidate. Do not infer loaded routing or send readiness from the on-disk
write. Canonical Bot Chat history does not qualify every own-default read path.

History of a profile whose own multiplex flag is absent or false (HMP
`test/flagless-profile-history`, root-reviewed, identical for absent and
false): a root-created routed conversation reads canonically and shows in the
Phone list (A); earlier history from that profile's standalone gateway is keyed
`agent:main`, stays intact and is readable by session id, but the canonical read
is empty (not an error) and the Phone list omits it (B). A later routed
conversation opens a new session and leaves the earlier one unlinked. The
route-only helper changed no profile byte, mtime, inode or mode and wrote no
flag or history. The fixture seeds real native runner, store and database
objects and reads canonical identity through them; it is not a gateway-loop,
authorization, transport or live-host run. Provenance is one archive, not a Git
checkout: its SHA cannot be attested, and it is bound only by read-bridge
fingerprint `d45f9a132819e7b18c9a653323409f386ff272e1824b90d0899cf3d45f11f627`
and source-tree digest
`4cff27fe80ccdbf092fecce4d95d6a1a41ce3ba490add244a155c4196a82c12e`. Do not
generalize it to other `ca705dbf` copies or builds. Route-only preparation is
not a legacy-history migration: a flag change or history rewrite is not an
authorized repair, and a safe fix needs a separate contract decision. The
generic upstream request is a stable, profile-scoped read contract for legacy
history that needs neither. Disposable-host gateway-loop and authorization
qualification is still open; do not call all history qualified. Evidence file:
`specs/005-new-profile-routing/C6-EVIDENCE.md` in that HMP branch. This entry is
from HMP evidence, not a fresh upstream refresh. A missing route `enabled` differs
from `enabled: null`; check the build's matcher rather than broadening a route.

Per-bot sending on this deployment also requires the qualified root HMP send
switch, a keyed root API listener bound to loopback, and each named profile's
own unique scoped key. Under the multiplexer that key authenticates its
`/p/<profile>/` route without starting a secondary listener. Verify this on the
exact build; it does not authorize copying the root key or starting a named
profile outside the multiplexer. Automatic credential provisioning is a new
host policy and write contract, not an existing plugin capability.

Native bot grants are user-scoped and can cover multiple paired devices.
Owner-only remote access cards need an explicit access-management role and
amendments to HMP's current host-only grant boundary; ordinary bot, scheduler
or model-setting access does not confer that role. Keep cards device-targeted
and outside the user-wide transcript. On `ca705dbf`, the profile-scoped pairing
CLI has no per-request deny, and its store uses process-local locks plus
separate pending/approved writes. Do not claim atomic remote settlement across
CLI and gateway writers. A vanished request without a grant is uncertain, not
success. Always select a validated profile explicitly with `-p`, validate a
request ID before approving, and verify resulting state without attributing
another writer's grant to the current ticket. Do not clear every pending
request to reject one.

The native `.env` helper is not a complete provisioning transaction: it lacks
cross-process locking/CAS, preserves existing file mode, can refuse managed
writes silently and may publish values to shared process environment. Require
a qualified profile-scoped writer, correct owner and private permissions before
automating unique keys. Inode and profile name alone are not a durable bot
identity; quarantine ambiguous name reuse rather than carrying old grants over.
These findings are source observations and proposed feature boundaries, not
released enrollment or access-card support.

For a live host, take a private backup and preserve comments, then check active
gateway work before an authorized drain-aware restart. Verify the fresh
listener and runtime process, then have the phone explicitly request access and
have the operator approve that exact request through the profile's own Hermes
CLI. This one incident does not refresh the skill against a newer upstream
snapshot.

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

On 2026-09-29, the owner-created hourly phone job persisted with `deliver:
bot-chat` and `context_from: [self]`. Its first live run completed `ok` and the
host recorded a `delivered` Bot Chat outcome with no error; the five-run counter
advanced to one. That verified scheduling and host-side delivery for the first
run only; the stored setting alone was not proof of continuity.

A later live second scheduled run completed, and its host-recorded input
contained the first answer, which is evidence of previous-run context
injection. The owner confirmed the first result was visible on the phone. A
saved checkbox is still not proof; check the recorded run input. Keep prompt,
output, and identifiers out of telemetry. A second phone-visible result and
the remaining pause/delete/refresh device checks are pending; the owner has
already confirmed cross-client schedule editing.

## Pinned plugin update behavior on Hermes `8afaab37`

`hermes plugins check-updates --json` reports a pinned custom plugin with
`update_available: false`, no `latest` revision, and a `pinned @ <sha>` reason;
that means the pin is fixed, not that no newer plugin exists. `hermes plugins
update <name>` refuses a pinned install and points to an explicit `plugins
install <source> --force --ref <full-sha>`. `hermes update` updates Hermes core
and can print plugin compatibility notices, but does not advance a separately
pinned plugin. A release-aware HMP check therefore needs reviewed release
metadata and a read-only comparison. Never automatically run a new plugin
revision during a core update; validate the candidate against the exact Hermes
build, preserve the old SHA for rollback, then explicitly install and restart.
Until release tags exist, comparing with the repository's `main` is misleading
when qualified feature work is still on another branch.

HMP draft PR #19 adds `hermes hmp update check` as a read-only command. It uses
the public GitHub latest-release tag, resolves its full commit (including
annotated tags), compares that commit's ancestry with the installed Git pin,
and reads four compatibility manifests at the immutable candidate SHA. It
does not fetch or execute candidate code, use a token, install, restart, or
write to the live home. A manifest's `listed` result means only that the
release names this exact Hermes build; runtime `compat`, per-bot `health`, and
a real client send remain required after install. As of 2026-09-29 there is
no published HMP release, so the check reports none. The first release and
isolated install/rollback exercise remain separate gates; do not call this
automatic update support.

The exact-ref plugin installer on this build twice failed a readability check
because Git pack files vanished during its temporary clone. A temporary Git
template containing `gc.auto=0` and `maintenance.auto=false` for that one
install prevented the race without editing the installed Hermes source. If the
failure recurs, confirm that the previous plugin and metadata stayed intact,
then prefer a narrow Git-maintenance workaround and verify the resulting pin,
gateway startup, and HMP compatibility. Do not treat the installer message's
suggested recursive permission change as the diagnosis of a vanished file.

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

On extracted stock-base `04fa849e` and experimental `7e8c8f07`, the session-chat stream did not register an approval notifier or emit `approval.request`; the `/v1/runs` path has a separate notifier and cannot silently replace a guarded Bot Chat send. HMP's mandatory real-route approval fixture failed on both builds. Verified 2026-09-30: untagged main `ac0cfa7db94cefa90cf3e35191f38b53888b9e17` did register the notifier and passed the isolated HMP real gateway/PTY fixture 17/17, including refusal of an exact-ID answer from the same device under a different profile. [HMP PR #44](https://github.com/MahdiHedhli/hermes-hmp/pull/44) is evidence only: it adds no runtime allowlist, no live approvals are enabled, and no released build is qualified. Keep the exact pending request ID, instance/profile/conversation binding, and authoritative Hermes settlement. The approved mobile visual design and read-only staged card have no production writer or answer controls; visual approval is not a protocol or release gate. The experimental `BasePlatformAdapter.handle_message` sets `event._gateway_accepted` when it spawns background processing, before durable admission or refusal is reported through `MessageEvent.admission_ticket` for `defer_policy="reject"`. Returning `202 submitted` from that flag alone can misstate a later refusal. Draft HMP PR #8 now waits for the ticket: only `admitted` reports submitted; known specific refusals report failure; `refused_other`, unfamiliar, absent, and timed-out outcomes remain `unknown` under the original cmid so replay does not send again. `refused_other` can represent `persist_failed`, and the ticket does not expose its reason, so it must not be treated as a definitive failure. Add a Phone chat transcript observation only after confirmed admission; otherwise a refused turn can appear delivered. Stock builds without the ticket API must not equate a false scheduling flag with refusal: exact `8afaab37` can retain a busy-queued event with that flag still false. Only strict True proves admission; False, missing or nonboolean remain unknown. For fixture sends after a gateway restart, wait until Hermes releases its startup-restore gate; an open listener and populated bot roster are too early, and the experimental build correctly reports `refused_draining` then. The isolated T8 Phone chat fixtures passed on both older builds, but full qualification failed on mandatory T7 there. Keep approvals disabled until the target build passes the current full fixture matrix and the explicit runtime-admission, device and exact-release gates; `ac0cfa7` above is not that.

## Approval process qualification

Verified against HMP draft [PR #53](https://github.com/MahdiHedhli/hermes-hmp/pull/53), commit
`8934993`, on 2026-09-30. This is plugin-specific development evidence, not an upstream Hermes
API promise or live approval enablement. AP-3/AP-4/AP-6, prompt producers and snapshot prompts
have an independent `approval_supported_builds.json` gate. Its shipped list is empty. Ordinary
guarded Bot Chat sends remain independent; a send-qualified build does not qualify approvals.

The draft binds its ordered source boundaries, fingerprints and git identity to the first
supported adapter factory call in a process. A first supported call with no matching approval
entry closes that process's approval lane. Adding an entry and recreating the listener cannot
replace this baseline; a full gateway process restart is required. An admitted process rechecks
current source and manifest before using its bounded successful-probe cache. Removing its entry
closes the next admission; restoring the exact baseline entry may reopen it. A different source
fingerprint cannot be admitted merely by updating the manifest in that running process.

`hermes hmp compat` reports an **on-disk** approval check, not running-process admission. This
is not process-start or loaded-memory attestation: the first supported factory use can occur
later, after modules were imported. Plugin unload/reimport can reset the module baseline. Full
gateway process restart remains mandatory after source or plugin changes. Do not infer a
qualified running bridge from unchanged listener configuration or an earlier successful check.

Root ran 1,364 local unit/tool tests with 12 skips and focused independent review cleared the
assigned draft process-binding defects. The earlier 17-case `ac0cfa7` gateway matrix above
predates this gate. A new pinned-source gateway/restart/reconnect matrix is still in progress;
no final current-gate receipt, physical-device result or release clearance is claimed. A
fixture-only receipt may be installed only into disposable plugin copies; it never adds a
shipped manifest entry. Archive/no-git lifecycle evidence does not validate the git-SHA branch.

**Update 2026-09-30.** HMP [PR #55](https://github.com/MahdiHedhli/hermes-hmp/pull/55) at `cc02892`
ran its tooling suite at 1,445 passed, 12 skipped, with 1 existing warning. The figures above
(1,364 tests, the 17-case matrix) stay as dated history. In run 8, an isolated Hermes `ac0cfa7`
with HMP runtime `8934993` passed all 7 stages and exactly 27 integration JUnit tests, with an
unsigned, fixture-only receipt. UUIDv7 wire client-message correlation was positive, and the
cross-profile case was negative, at the moment of observation; that is not proof of later
persistence. This matrix does not qualify draft PR #54 runtime `4b4626a`, which turns a definitive
false into `applied:false`/refusal. A `None` or unfamiliar outcome must stay `unknown`.

The manifest is still empty, so no live admission exists. A full gateway process restart is
required; resetting the listener is not enough. HMP's non-strict AP-6 accepts broader client
message IDs, but the bridge correlates on UUIDv7. The earlier fixture's UUIDv4 ID was corrected
to UUIDv7; it was a fixture defect, not mobile client behavior. Do not assume a current release tag. The final candidate
combination, physical devices, and the release gate remain open.

**Admission ambiguity found in exact `8afaab37`.** The stock adapter initializes
`_gateway_accepted=False`; its busy queue-text debounce path can retain an event without
changing that flag. A false scheduling flag therefore does not prove refusal. Treat it as
unknown on builds without an admission ticket, preserve the same idempotency key, and do not
invite an automatic or new-key resend. Ticket builds still require their definitive reported
outcome. HMP [draft PR #56](https://github.com/MahdiHedhli/hermes-hmp/pull/56) at `86f2a23`
fixes this, with a causal real-adapter regression and independent review; root's full suite
passed 1,493 tests with 13 existing skips. It is not a confirmed live duplicate incident.

**Current fixture evidence.** Archive run 10 and independent Git-install run 2 against exact
`8afaab3703e336d72a72c812dd2dd249f04f166a`, runtime `86f2a23`, each passed all seven stages
and the exact 27 required integration JUnit cases without failures, errors or skips. Draft
[PR #58](https://github.com/MahdiHedhli/hermes-hmp/pull/58) adds the independent Git lane;
its root suite passed 1,558 tests with 13 existing skips. Unsafe metadata is rejected before
copy or retargeting writes. An archive receipt never qualifies a Git installation. Both
unsigned receipts are disposable fixture evidence, not live/device/release admission or
loaded-memory attestation; production approval entries remain empty.

**Git identity correction.** In HMP [draft PR #57](https://github.com/MahdiHedhli/hermes-hmp/pull/57),
only truly absent `.git` metadata yields a fingerprint-only archive identity. Present but
unresolvable metadata, including a dangling link, is unidentifiable. Root's suite passed
1,501 tests with 13 existing skips and focused review cleared the bounded fix. The earlier
matrices do not qualify this new runtime diff; combined qualification remains required.
Git HEAD is metadata, not object-store integrity or loaded-module attestation. An existing
Python 3.11/3.12 symlink-loop exception can surface in direct-send handling but grants no
capability; that availability limitation remains recorded outside this fix.

### Offline fixture setup diagnostics

Evidence: HMP draft [PR #60](https://github.com/MahdiHedhli/hermes-hmp/pull/60) at `d8b8b08`
and its Amendment 4 (`specs/005-approval-process-matrix/amendment-4-setup-diagnostics.md`).
This is fixture-tooling evidence, not runtime, release or device qualification.

- Separate an offline fixture-seed setup error, which happens before any gateway starts, from a
  real 45 s listener-readiness failure. They need different diagnosis and fixes.
- `subprocess.run(capture_output=True, check=True)` keeps stdout/stderr on `CalledProcessError`,
  but an ordinary failure report may omit them; retain them privately before the process exits.
  Pytest traceback frames can also serialize a helper's caller environment. Never dump raw logs
  or environment into reports.
- Retain diagnostics only in a validated private directory through a held descriptor, with a
  0600 file, and give the child an explicit environment allowlist. Both are separate from
  bounding parent RAM: a 64 KiB retained tail does not limit `capture_output` memory.
- Root passed 312 fixture/CI tests with configured Ruff clean. Three formerly failing T7 cases then
  passed fresh with zero errors or skips against exact Git `8afaab3703e336d72a72c812dd2dd249f04f166a`, with the source/plugin
  snapshot unchanged. That partial run wrote no final receipt and is not the 27-case, seven-stage,
  runtime or release qualification. The original cause stays unknown.
- Still open: ambient parent environment reaching other helpers, unbounded in-memory capture,
  and `--showlocals` exposure. A new complete qualification is pending. The archive and Git
  lanes keep their separate gates.

## Chat media and attachments

Root read-only source verification on 2026-09-30 against exact Hermes
`ca705dbf7ef86425b381b542712aff310f1ee52c`; this is not a claim about other builds.

**Rendering gap.** A linked HTTPS Markdown image string reaches mobile, but the mobile renderer
shows it as literal text. That is our app gap. Do not treat all media as upstream-blocked.

**Plugin building blocks.** Hermes already has `MessageEvent.media_urls` and `media_types`,
the native `BasePlatformAdapter` send methods for image, file, video, document, and audio, and
module-level cache helpers in `gateway/platforms/base.py`: `cache_document_from_bytes`,
`cache_image_from_bytes`, `cache_media_bytes`. `cache_media_from_bytes` is absent (stale name), and
a different `cache_media_bytes` exists in `media_cache.py`; pin the module. HMP's Phone-chat event is
text-only and it overrides no native outbound media hook, and its bridge passes text-only parts.
Bounded native delivery could use these hooks without core changes, but it still needs
qualification. See [Deliverable Mode](https://hermes-agent.nousresearch.com/docs/user-guide/features/deliverable-mode),
[Adding Platform Adapters](https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters), and the exact source
at [`api_server.py#L3463-L3489`](https://github.com/NousResearch/hermes-agent/blob/ca705dbf7ef86425b381b542712aff310f1ee52c/gateway/platforms/api_server.py#L3463-L3489).

**Isolated native primitive evidence** (archive provenance `ca705dbf`, not a re-attested Git
install; root reviewed and reproduced 73 checks, with 30 focused tests on HMP `9d91ca1`):
- The document helper contained hostile filenames but has no size/type bound. Under umask 022
  its file was 0644 and directory 0755; native does not enforce private cache modes. Newlines
  survive in names and reach the prepared note. Enforce input bounds, generated names and
  private storage before delivery. Inbound preparation trusts supplied media paths, so accept
  only paths the plugin created in its scoped cache.
- The image cap and magic check rejected cap+1 and invalid magic, but a magic-only undecodable
  body was accepted. Enforce decode, pixel and metadata policy before the helper. Rejected-byte
  content appeared in the helper's error; do not log or return that native error verbatim.
- Unset/None `media_text_inlined` on text makes the same content-included claim as True, without
  inlining. Set `[False]` when no content was inlined; binary notes ignore the flag.
- The real runner queue method merges matching-scope PHOTO/TEXT; DOCUMENT uses FIFO. A merge
  retains only the first client id. Different scope or gateway-control flags prevented merge.
  The full busy authorization/ack/steer/admission path was not exercised.
- Real flush helpers and SessionDB with controlled agent shapes stored document host-path notes
  and projected image parts plus string override to caption plus `[screenshot]`, without media
  identity. This was not a real agent turn or HMP read-back. Profile re-homing, model enrichment,
  cache sweep and audio/video remain unproven; do not promise complete attachment history.

This discovery does not qualify a supported release, freeze an upload contract or admit a live
host. The fixture used disposable roots and Python socket denial, not an OS network sandbox.
Recheck the exact target build and the complete adapter path before relying on these primitives.
Evidence: [native fixture](https://github.com/MahdiHedhli/hermes-hmp/blob/test/phone-attachment-native-primitives/docs/research/phone-attachment-native-primitives-2026-09-30.md).

**Canonical Bot Chat.** `api_server._session_chat_user_message` accepts text and image parts but
rejects file parts. `_admit_to_live_bot_chat` returns `None` for a non-string message, and
`tools/bot_live_delivery.deliver_to_live_owner` requires `str`. Do not submit multimodal content
to a Desktop-owned canonical session through a handoff skip, or another owner may be caused to
act. This is a source finding, not an exercised exploit. Attachment-aware, single-owner canonical
admission needs an upstream change or an equally safe, qualified route. Do not silently fall
back to Phone chat.

**Existing alternatives that do not fit.** Browser control `/v1/artifacts` requires its flag and
a Bearer token, profile/principal/family binding, a one-shot download TTL, and in-memory
receipts. It is not durable chat history, so do not enable browser control for attachments.
`_resolve_media_to_data_urls` converts bounded, validated `MEDIA` images for its own API
completions only; it is not a Desktop mailbox or HMP persistent-history path.

**Design requirements.** Use profile-, conversation-, and device-bound opaque handles with native
validation. Offer no raw-path endpoint and no text-grant authority. Never forward Hermes or
device credentials to external media hosts. Bound MIME types, bytes, pixels, redirects, and
network access. If persistent media caching is introduced, encrypt it and support purge.
Preserve durable pending state with no automatic retry.

## Session snapshot consistency

On source `8afaab3703e336d72a72c812dd2dd249f04f166a`, `SessionDB.get_session` and `get_messages` borrow separate read contexts and expose no public read transaction spanning both. A current-session eligibility check followed by a messages read can race a fork, lineage, or session mutation. Pre/post checks do not prove one snapshot (ABA: state can change and return). Prefer an upstream transactional selector-plus-messages primitive; do not bypass Hermes with copied private SQLite schema or lineage logic.

[HMP PR #49](https://github.com/MahdiHedhli/hermes-hmp/pull/49) improves scoped canonical selection and per-request ref recheck but does not close this gap. [HMP PR #51](https://github.com/MahdiHedhli/hermes-hmp/pull/51) keeps extra session-browsing routes absent by default and requires an explicit boolean `true` opt-in for controlled testing; malformed or merely truthy config does not enable them and the picker stays hidden. That gate does not disable canonical Bot Chat.
