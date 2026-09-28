# Hermes Developer Workflows

Common playbooks. Use docs and area `AGENTS.md` from the checkout whose behavior the task must support.

## W1 — Orient on a subsystem

1. Load this skill (`hermes-developer`).
2. Open `references/architecture-snapshot.md` + matching page in `website/docs/developer-guide/`.
3. Search code for entry symbols (`AIAgent`, `registry.register`, `GatewayRunner`, …), then follow facade exports into owning siblings.
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
5. `scripts/run_tests.sh` + manual path in an isolated home.
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
4. `hermes plugins validate`, `hermes plugins list`, and exercise the real registration path.
5. Third-party products: publish outside core tree.

## W6 — Keep this skill current

1. Compare latest official docs and source in an isolated checkout; record its commit.
2. `HERMES_AGENT_REPO=<checkout> python3 <skill>/scripts/refresh_from_docs.py`
3. Diff `references/_doc_headings.md` + `LAST_REFRESH.md`
4. Patch SKILL/references if architecture or ladders changed; validate the skill.

## W7 — Dashboard / web ops (ops, not core)

For dashboard development, use the current dashboard/desktop plugin guides and area `AGENTS.md`; for routine operation, use the user guide.

## Source-of-truth priority

1. User instructions and the target checkout's `AGENTS.md` / area `AGENTS.md`.
2. Version-matched source and docs for that checkout, or latest official source and docs when latest upstream is requested.
3. On a disagreement, trace the executable path and note which commit or version the conclusion covers.
