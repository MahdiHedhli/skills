# Extension Surface Map

Choose the highest (least footprint) rung that solves the problem correctly.

## Decision table

| Need | Prefer | Avoid |
|------|--------|-------|
| Workflow / CLI wrapper / docs for existing tools | **Skill** | New core tool |
| Personal or project-local tool | **Plugin** in `~/.hermes/plugins/` or project `.hermes/plugins/` | Editing core `tools/` |
| Third-party SaaS / observability / vendor product | **Standalone plugin repo** | PR into core `plugins/` |
| Structured I/O only when prerequisite configured | **Service-gated tool** (`check_fn`) | Always-on core tool |
| External system with its own MCP server | **MCP** in config / catalog | Reimplementing as core |
| New chat channel (Telegram-like) | **Platform adapter** | Forking gateway core |
| OpenAI-compatible API key provider | **Model provider plugin** | Full built-in provider checklist |
| Non-OpenAI protocol / special auth / curated catalog | **Built-in provider** (adding-providers) | Hacks in run_agent only |
| Memory backend | **Memory provider plugin** (single-select) | Parallel competing memory tools in core |
| Compression strategy | **Context engine plugin** (single-select) | Mid-loop prompt rewrites |
| Image / video / web-search / browser / secrets backend | Matching **typed provider plugin** | Hardcoding one vendor in core |
| TTS / STT custom CLI | **Config-driven** custom command | New Python tool unless needed |
| Gateway lifecycle side effects | **Gateway hooks** (`~/.hermes/hooks/`) or shell hooks | Monkeypatching `gateway/run.py` |
| Slash UX | **CommandDef registry** | Ad-hoc string matchers only in one surface |
| Scheduled agent work | **Cron** / skill **blueprint** | Long-lived parent `delegate_task` |

## Skill vs tool

**Skill** when: instructions + shell + existing tools suffice (git, docker, arxiv, PDF, email CLIs).

**Tool** when: API keys + custom processing, binary/streaming, or must run precisely every time (browser, TTS, vision).

**Plugin tool** when: same as tool but not shipping in core.

## Built-in tool checklist

1. `tools/<name>_tool.py` — handler, schema, `check_fn`, `registry.register`
2. `toolsets.py` — `_HERMES_CORE_TOOLS` or named toolset
3. Optional `OPTIONAL_ENV_VARS` in `hermes_cli/config.py`
4. Handler returns JSON string; errors as `{"error": "..."}`
5. Manual: `hermes chat -q "…"`

## Plugin layout (general)

```
~/.hermes/plugins/<name>/
  plugin.yaml          # name, version, provides_tools, provides_hooks, requires_env
  __init__.py          # register(ctx) wiring
  schemas.py           # OpenAI-style schemas (description quality matters)
  tools.py             # handlers(args, **kwargs) -> JSON str
  skills/…             # optional bundled skills
  data/…               # optional assets
```

Discovery sources: user `~/.hermes/plugins/`, project `.hermes/plugins/`, pip entry points.

## Built-in provider checklist (summary)

Always: `auth.py`, `models.py`, `runtime_provider.py`, `main.py` menus, `auxiliary_client.py`, `model_metadata.py`, tests, website docs.

Native protocol additionally: `agent/<provider>_adapter.py`, `run_agent.py` branches, maybe `pyproject.toml` SDK.

Simple API-key OpenAI-compatible: prefer `plugins/model-providers/<name>/` + `register_provider(profile)` only.

## Platform adapter

Implement adapter under `gateway/platforms/`; follow adding-platform-adapters + `ADDING_A_PLATFORM.md` if present. Wire setup UX (`hermes gateway setup`, env, allowlists).

## Slash command

1. `CommandDef` in `hermes_cli/commands.py`  
2. CLI handler in `cli.py`  
3. Optional gateway handler in `gateway/run.py`  
Aliases only need the `aliases` tuple — all menus derive automatically.

## Agent-intercepted tools

Do not re-route pure registry tools that need agent state without understanding intercepts in `run_agent.py`: `todo`, `memory`, `session_search`, `delegate_task`.
