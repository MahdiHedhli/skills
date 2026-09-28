# Architecture Snapshot

Checked against the official architecture, agent-loop, and gateway docs plus source at `e408d363393ccb72267e67bcccf4f8954b438cd9` (2026-09-28). Recheck the target checkout before using file locations as instructions.

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
run_agent.py           # AIAgent facade; loop in agent/conversation_loop.py and turn_*.py
model_tools.py         # discovery + handle_function_call
toolsets.py            # groupings / presets
hermes_state.py        # SessionDB facade; hermes_state_*.py siblings
hermes_constants.py    # get_hermes_home()
agent/                 # prompt, compression, memory ABC, adapters
hermes_cli/            # CLI, config, auth, plugins, commands registry
tools/                 # one module per tool; registry auto-discover
tools/environments/    # local, docker, ssh, modal, daytona, singularity
gateway/               # run.py facade, run_*.py phases, session*.py, shared/legacy adapters
plugins/platforms/     # most bundled messaging adapters
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

1. Build turn context and preserve the conversation's cached prompt/tool prefix.
2. Apply compression when current policy calls for it; keep role and tool-call structure valid.
3. Resolve provider/API mode and make an interruptible call.
4. Dispatch tool calls and append results through the current turn modules.
5. Finalize, persist, and report usage. Check `agent/conversation_loop.py` and `agent/turn_*.py` for exact ordering.

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

- Compression policy and thresholds evolve; read the current compressor and session lifecycle docs.
- Preserve role alternation and tool-call/result pairing.
- Compression may create child session lineage; follow it when resolving conversation history.

## Callbacks (platform glue)

`tool_progress_callback`, `thinking_callback`, `reasoning_callback`, `clarify_callback`, `step_callback`, `stream_delta_callback`, `tool_gen_callback`, `status_callback`
