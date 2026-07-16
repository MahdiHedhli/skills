---
name: hermes-developer
description: "Develop and extend Hermes Agent — architecture, contribution, tools/plugins/skills/providers, and keep this skill current with official docs."
version: 1.1.0
author: Mahdi Hedhli
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, developer, architecture, contributing, plugins, tools, skills, providers]
    homepage: https://github.com/MahdiHedhli/skills/tree/main/skills/hermes-developer
    related_skills: [hermes-agent]
---

# Hermes Developer

Authoritative skill for **building on Hermes Agent itself**: core contributions, plugins, tools, skills, providers, adapters, and internals.

For day-to-day **configure / setup / use** of an installed Hermes instance, load `hermes-agent` instead. Use this skill when the task is code, PRs, extension surfaces, or understanding how the platform works.

**Live docs (source of truth):** https://hermes-agent.nousresearch.com/docs/developer-guide/  
**Local checkout (preferred when present):** `$HERMES_HOME/hermes-agent` → usually `~/.hermes/hermes-agent`  
**In-repo AI/dev guide:** `$HERMES_HOME/hermes-agent/AGENTS.md`  
**Doc sources:** `$HERMES_HOME/hermes-agent/website/docs/developer-guide/`

If this skill and live docs disagree, **docs win**. Then refresh this skill (see [Keep this skill current](#keep-this-skill-current)).

---

## Sacred design constraints

Every change is reviewed through these lenses (from `AGENTS.md` + Architecture):

1. **Prompt caching is sacred.** Do not mutate past context, swap toolsets, or rebuild the system prompt mid-conversation. Exception: explicit context compression. System prompt must stay byte-stable for the life of a conversation (except user actions like `/model`).
2. **Narrow waist, wide edges.** Every *model tool* is sent on every API call. Prefer CLI + skill → service-gated tool (`check_fn`) → plugin → MCP catalog → new core tool (last resort). Product surface (platforms, providers, TUI, desktop) may grow aggressively at the edges.
3. **Strict message alternation.** Never two assistant or two user messages in a row. Only consecutive `tool` results are allowed. Never inject a synthetic user message mid-loop.
4. **Profile-safe paths.** Never hardcode `~/.hermes`. Use `get_hermes_home()` / `display_hermes_home()` from `hermes_constants`.
5. **Secrets vs config.** API keys/tokens → `.env`. Behavioral settings → `config.yaml`. No new `HERMES_*` env vars for non-secret config.

### Footprint ladder (new capability)

1. Extend existing code  
2. CLI command + skill (zero model-tool footprint)  
3. Service-gated tool with `check_fn`  
4. Plugin (`~/.hermes/plugins/` or pip entry point)  
5. MCP server in catalog  
6. New core tool (only if fundamental and unreachable via terminal/file/MCP)

Third-party product integrations (vendor SaaS, observability backends, etc.) ship as **standalone plugin repos**, not under core `plugins/`.

---

## Architecture map

```
Entry: CLI (cli.py) | Gateway (gateway/run.py) | ACP | Batch | API Server | Library
                    ↓
              AIAgent (run_agent.py)
   Prompt Builder │ Provider Runtime │ Tool Dispatch (model_tools + registry)
   Compression    │ 3 API modes      │ 70+ tools / ~28 toolsets
                    ↓
   SessionDB (SQLite+FTS5)     Tool backends (terminal×6, browser×5, web×4, MCP…)
```

| Subsystem | Primary files | Doc |
|-----------|---------------|-----|
| Agent loop | `run_agent.py` | agent-loop |
| Prompt assembly | `agent/prompt_builder.py`, `agent/system_prompt.py` | prompt-assembly |
| Caching / compression | `agent/prompt_caching.py`, `agent/context_compressor.py` | context-compression-and-caching |
| Providers | `hermes_cli/runtime_provider.py`, `hermes_cli/auth.py` | provider-runtime, adding-providers |
| Tools | `tools/registry.py`, `model_tools.py`, `toolsets.py` | tools-runtime, adding-tools |
| Sessions | `hermes_state.py`, `gateway/session.py` | session-storage |
| Gateway | `gateway/run.py`, `gateway/platforms/*` | gateway-internals |
| Plugins | `hermes_cli/plugins.py`, `plugins/*` | plugins |
| Cron | `cron/jobs.py`, `cron/scheduler.py` | cron-internals |
| ACP | `acp_adapter/` | acp-internals |
| Slash commands | `hermes_cli/commands.py` → CLI/gateway consumers | extending-the-cli |
| Skills | `skills/`, `optional-skills/`, hub | creating-skills |

**API modes:** `chat_completions` (default OpenAI-compatible) · `codex_responses` · `anthropic_messages`

**Agent-loop intercepted tools** (stateful; not pure registry dispatch): `todo`, `memory`, `session_search`, `delegate_task`.

**Tool discovery:** any `tools/*.py` with top-level `registry.register()` is auto-imported. Handlers **must** return JSON strings; errors as `{"error": "..."}` never raised.

**Prompt tiers (cached):** `stable` (identity, tools, skills, env) → `context` (project files) → `volatile` (memory/profile/timestamp). Ephemeral per-call overlays are separate and must not break the stable prefix.

---

## Task routing — what to load / where to edit

| Goal | Path | Start here |
|------|------|------------|
| Custom tool without core PR | Plugin | docs: plugins; `~/.hermes/plugins/<name>/` |
| Built-in core tool | Core PR | `tools/your_tool.py` + `toolsets.py` |
| Procedural capability | Skill | `SKILL.md` under skills/ or hub |
| Inference backend (simple API key) | Model-provider plugin | `plugins/model-providers/` |
| First-class built-in provider | Core PR | adding-providers checklist |
| Messaging channel | Platform adapter | `gateway/platforms/`, adding-platform-adapters |
| Memory / context engine / secrets / image / video / web / browser backend | Typed plugin | matching `*-provider-plugin` / `context-engine-plugin` doc |
| External tools as-is | MCP | `mcp_servers` in config.yaml |
| Slash command | Registry | `CommandDef` in `hermes_cli/commands.py` + handlers |
| Cron automation | Skill blueprint or cron API | creating-skills blueprints; cron-internals |
| Programmatic embed | Library | programmatic-integration |

Full interface map lives in references and the plugins guide's "If you want to add…" table.

---

## Contribution workflow (condensed)

**Priorities:** bugs → cross-platform → security → robustness → skills → tools (rare) → docs.

**Dev bootstrap (preferred):**
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
cd "${HERMES_HOME:-$HOME/.hermes}/hermes-agent"
uv pip install -e ".[all,dev]"
# optional: npm install  # browser tools / docs site
scripts/run_tests.sh
```

**PR hygiene:**
- Branch: `fix/…`, `feat/…`, `docs/…`, `refactor/…`
- Conventional commits: `fix(scope): …` scopes include `cli`, `gateway`, `tools`, `skills`, `agent`, `security`
- Focused PRs; reproduce on current `main`; fix the whole bug class
- Tests: behavior contracts / invariants, not change-detector snapshots of lists or counts
- E2E for resolution chains, security boundaries, remote backends — real imports + temp `HERMES_HOME`
- Cross-platform: no unguarded `SIGKILL`/`setsid`/`killpg`; UTF-8 explicit; `pathlib`
- Windows: `scripts/check-windows-footguns.py` when touching I/O, processes, terminals

**Verify premise before "fixing":** intentional isolation (e.g. profile islands) is not a gap. Read `git log -p -S` for original intent.

---

## Recipes (minimal)

### Skill (preferred for most capability)
See creating-skills. Structure: `SKILL.md` + optional `scripts/`, `references/`, `templates/`, `assets/`.  
Secrets → `required_environment_variables`; non-secrets → `metadata.hermes.config`.  
Template tokens: `${HERMES_SKILL_DIR}`, `${HERMES_SESSION_ID}`.

### Built-in tool
1. `tools/foo_tool.py` — handler + schema + `check_fn` + `registry.register(...)`
2. Add name to `_HERMES_CORE_TOOLS` or a toolset in `toolsets.py`
3. Optional: `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`
4. Test: `hermes chat -q "…"`

### Plugin
```bash
mkdir -p ~/.hermes/plugins/myplugin
# plugin.yaml + __init__.py register(ctx) + handlers returning JSON strings
hermes plugins list
```
Hooks: `pre_tool_call` / `post_tool_call` and others per plugins guide. Do not patch core files from plugins — widen the generic surface if needed.

### Slash command
1. `CommandDef` in `COMMAND_REGISTRY` (`hermes_cli/commands.py`)
2. Handler in `cli.py` `process_command`
3. Optional gateway handler in `gateway/run.py`  
Help, autocomplete, Telegram menu, Slack map all derive from the registry.

### Tests
```bash
scripts/run_tests.sh
python -m pytest tests/tools/ -q -o 'addopts='
```
Suite auto-redirects `HERMES_HOME` to temps — never point tests at real home.

---

## Keep this skill current

When Hermes docs or `AGENTS.md` change, or before a non-trivial platform task, **refresh this skill**.

### Refresh procedure (mandatory when docs may have drifted)

1. **Locate sources**
   - Local: `${HERMES_HOME:-$HOME/.hermes}/hermes-agent`
   - Docs tree: `website/docs/developer-guide/**/*.md`
   - AI guide: `AGENTS.md`
   - Live index: https://hermes-agent.nousresearch.com/docs/developer-guide/contributing

2. **Pull latest if git-managed**
   ```bash
   cd "${HERMES_HOME:-$HOME/.hermes}/hermes-agent" && git fetch && git log -1 --oneline origin/main
   # optional: git pull --ff-only  (only if user wants install tree updated)
   ```

3. **Run the refresh script** (writes reference snapshots + stamp)
   ```bash
   bash ${HERMES_SKILL_DIR}/scripts/refresh_from_docs.sh
   # or: python ${HERMES_SKILL_DIR}/scripts/refresh_from_docs.py
   ```

4. **Diff & patch**
   - Read `references/LAST_REFRESH.md` and changed reference files
   - Patch this `SKILL.md` if ladders, file maps, or recipes drifted
   - Use `skill_manage(action='patch')` for surgical updates; full `edit` only for major overhauls

5. **Also update** the user-facing `hermes-agent` skill if CLI/commands/config surfaces changed (related skill).

6. **Verify**
   - Spot-check one architecture claim against source (`run_agent.py` or docs)
   - Confirm doc URLs still resolve (local files or browser)

### When to refresh without being asked
- User says Hermes was updated / `hermes update` ran
- A procedure in this skill fails against real code
- Contributing to Hermes and docs are older than ~2 weeks vs local `git log`
- New extension surface appears (new plugin kind, new API mode, new entry point)

### What NOT to bake into this skill
- Full verbatim copies of every developer page (use references + links)
- User config walkthroughs (belongs in `hermes-agent`)
- Stale model lists / tool counts as hard assertions (counts change; say "see toolsets.py")

---

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Mid-conversation tool enable | Won't apply until new session — preserves cache |
| New core tool "because it's easier" | Use skill/plugin/MCP first |
| Hardcoded `~/.hermes` | Breaks profiles — use `get_hermes_home()` |
| Handler returns dict / raises | Always `json.dumps`; catch and return error JSON |
| Lazy pagination on instructional tools | Models skip page 2 — load fully |
| Plugin in core tree for third-party SaaS | Standalone repo + `~/.hermes/plugins/` |
| Change-detector tests | Assert invariants, not enumeration counts |
| Synthetic user msg mid-loop | Breaks alternation / providers reject |
| Venv inside agent workspace | Agent may `rm -rf` it — keep venv outside tree |

---

## Quick links

| Topic | URL |
|-------|-----|
| Contributing | https://hermes-agent.nousresearch.com/docs/developer-guide/contributing |
| Architecture | https://hermes-agent.nousresearch.com/docs/developer-guide/architecture |
| Agent loop | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Prompt assembly | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |
| Caching | https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching |
| Sessions | https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage |
| Provider runtime | https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime |
| Programmatic | https://hermes-agent.nousresearch.com/docs/developer-guide/programmatic-integration |
| Adding tools | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-tools |
| Adding providers | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-providers |
| Platform adapters | https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters |
| Plugins | https://hermes-agent.nousresearch.com/docs/developer-guide/plugins |
| Creating skills | https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills |
| Extending CLI | https://hermes-agent.nousresearch.com/docs/developer-guide/extending-the-cli |
| Tools runtime | https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime |
| Gateway | https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-internals |
| Cron | https://hermes-agent.nousresearch.com/docs/developer-guide/cron-internals |
| ACP | https://hermes-agent.nousresearch.com/docs/developer-guide/acp-internals |
| Trajectory | https://hermes-agent.nousresearch.com/docs/developer-guide/trajectory-format |
| GitHub | https://github.com/NousResearch/hermes-agent |

## Reference files

| File | Purpose |
|------|---------|
| `references/docs-index.md` | Full developer-guide catalog + reading order |
| `references/extension-map.md` | Skill vs tool vs plugin vs provider decision table |
| `references/architecture-snapshot.md` | Condensed architecture / loop / prompt tiers |
| `references/contributing-checklist.md` | PR / security / anti-patterns checklist |
| `references/workflows.md` | Agent playbooks (orient, add capability, refresh) |
| `references/LAST_REFRESH.md` | Last docs sync stamp |
| `references/_doc_headings.md` | Drift-detection headings snapshot |
| `scripts/refresh_from_docs.py` | Re-sync from local `$HERMES_HOME/hermes-agent` docs |

**Related skill:** `hermes-agent` — install, configure, CLI, gateway, day-to-day ops.
