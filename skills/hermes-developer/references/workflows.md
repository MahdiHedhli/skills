# Hermes Developer Workflows

Common agent playbooks. Prefer local docs under `$HERMES_HOME/hermes-agent` when available.

## W1 — Orient on a subsystem

1. Load this skill (`hermes-developer`).
2. Open `references/architecture-snapshot.md` + matching page in `website/docs/developer-guide/`.
3. Grep code for entry symbols (`AIAgent`, `registry.register`, `GatewayRunner`, …).
4. Do **not** rely on tool counts / model lists baked into this skill.

## W2 — Add capability (choose rung)

1. Consult `references/extension-map.md` footprint ladder.
2. Default path:
   - workflow → **skill**
   - personal tool → **plugin**
   - third-party SaaS → **standalone plugin repo**
   - fundamental always-on → only then **core tool**
3. Implement smallest surface; wire setup UX (`hermes setup` / tools / plugins) if user-facing.

## W3 — Core PR bugfix

1. Reproduce on current `main`.
2. Find line of manifestation + sibling paths.
3. Confirm intentional design isn't the "bug" (`git log -p -S`).
4. Fix + invariant tests (not snapshot counts).
5. `scripts/run_tests.sh` + manual path.
6. Conventional commit + focused PR.

## W4 — Skill authoring

1. Frontmatter: name, description, version, tags; optional platforms / requires_* / config / env.
2. Body: When to Use → Quick Reference → Procedure → Pitfalls → Verification.
3. Bundle scripts under `scripts/`; use `${HERMES_SKILL_DIR}`.
4. Secrets vs config separation.
5. Test: `hermes chat --toolsets skills -q "Use the X skill to …"`.

## W5 — Plugin authoring

1. `~/.hermes/plugins/<name>/plugin.yaml` + `__init__.py` `register(ctx)`.
2. Schemas describe **when** the model should call the tool.
3. Handlers: `(args, **kwargs) -> JSON str`; never raise.
4. `hermes plugins list` + exercise tool in chat.
5. Third-party products: publish outside core tree.

## W6 — Keep this skill current

1. `python ${HERMES_SKILL_DIR}/scripts/refresh_from_docs.py`
2. Diff `references/_doc_headings.md` + `LAST_REFRESH.md`
3. Patch SKILL/references if architecture or ladders changed
4. If user CLI/config docs drifted, patch related skill `hermes-agent`

## W7 — Dashboard / web ops (ops, not core)

User-facing: `hermes dashboard` (default http://127.0.0.1:9119). Needs `.[web,pty]`.  
Not the focus of this skill — see user guide web-dashboard + `hermes-agent` skill.

## Source-of-truth priority

1. Live docs site (what users see after update)
2. Local `website/docs/developer-guide/` + `AGENTS.md` (version-matched to install)
3. Source code when docs conflict → fix docs/skill after verifying code
