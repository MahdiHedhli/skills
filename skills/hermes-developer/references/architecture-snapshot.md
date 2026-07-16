# Architecture Snapshot

Condensed from Architecture + Agent Loop + Prompt Assembly docs. Refresh when those change.

## Entry points → one agent core

| Entry | File | Notes |
|-------|------|-------|
| Interactive CLI | `cli.py` | HermesCLI, prompt_toolkit / Rich |
| TUI | `ui-tui` + `tui_gateway` | Ink ↔ JSON-RPC ↔ AIAgent |
| Gateway | `gateway/run.py` | Long-running multi-platform |
| ACP | `acp_adapter/` | IDE (VS Code, Zed, JetBrains) |
| Batch | `batch_runner.py` | Trajectories / bulk |
| Library | programmatic API | `AIAgent.chat` / `run_conversation` |

Platform differences live in the **entry point**, not inside `AIAgent`.

## Directory anchors

```
run_agent.py           # AIAgent loop
model_tools.py         # discovery + handle_function_call
toolsets.py            # groupings / presets
hermes_state.py        # SQLite sessions + FTS5
hermes_constants.py    # get_hermes_home()
agent/                 # prompt, compression, memory ABC, adapters
hermes_cli/            # CLI, config, auth, plugins, commands registry
tools/                 # one module per tool; registry auto-discover
tools/environments/    # local, docker, ssh, modal, daytona, singularity
gateway/platforms/     # ~20 adapters
plugins/               # typed plugin packages (memory, context_engine, …)
skills/                # bundled
optional-skills/       # official but opt-in
cron/                  # jobs + scheduler
website/docs/          # Docusaurus
tests/                 # large pytest suite
```

## Import / registration chain

```
tools/registry.py
  ↑ tools/*.py (registry.register at import)
  ↑ model_tools.py (discover_builtin_tools)
  ↑ run_agent / cli / batch / environments
```

Then MCP tools and plugin tools register.

## Turn lifecycle (agent loop)

1. Append user message  
2. Build/reuse cached system prompt  
3. Preflight compression if needed (~50% context)  
4. Build API messages for api_mode  
5. Ephemeral layers (budget/pressure) — not durable system rebuilds  
6. Prompt cache markers (Anthropic)  
7. Interruptible API call  
8. Tool calls → dispatch (concurrent pool unless interactive) → append tool results → loop  
9. Final text → persist session, flush memory  

## Message rules

Internal format is OpenAI-style `role`/`content`/`tool_calls`.  
Alternation: User↔Assistant; tool batches after assistant tool_calls only.

## Prompt tiers

| Tier | Contents |
|------|----------|
| stable | SOUL/identity, tool guidance, skills index, env/platform hints |
| context | caller system_message, AGENTS.md / CLAUDE.md / .cursorrules / .hermes.md |
| volatile | MEMORY.md, USER.md, external memory provider, timestamp/session line |

Skills live in **stable**. Memory snapshots in **volatile**. Both are still part of the cached system prompt for the session — do not thrash them mid-conversation.

## Design principles

| Principle | Practice |
|-----------|----------|
| Prompt stability | No mid-convo toolset/system-prompt swaps |
| Observable execution | Tool callbacks for CLI spinner / gateway progress |
| Interruptible | API + tools cancellable |
| Platform-agnostic core | One AIAgent for all surfaces |
| Loose coupling | Registries + check_fn gating |
| Profile isolation | Separate HERMES_HOME per profile |

## Data flows

**CLI:** input → `run_conversation` → tools → display → SessionDB  

**Gateway:** adapter event → auth → session key → AIAgent → adapter delivery  

**Cron:** tick → fresh AIAgent (no history) → skills context → prompt → deliver → update job  

## Compression notes

- Preflight ~50%; gateway between-turns more aggressive (~85%)  
- Flush memory first; summarize middle; protect last N messages; keep tool pairs intact  
- Compression creates child session lineage  

## Callbacks (platform glue)

`tool_progress_callback`, `thinking_callback`, `reasoning_callback`, `clarify_callback`, `step_callback`, `stream_delta_callback`, `tool_gen_callback`, `status_callback`
