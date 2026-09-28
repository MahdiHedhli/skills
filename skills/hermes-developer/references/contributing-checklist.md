# Contributing Checklist

Condensed from contributing.md + AGENTS.md. Use before opening a Hermes core PR.

## Priorities (highest first)

1. Bug fixes (crashes, wrong behavior, data loss)
2. Cross-platform (macOS, Linux distros, WSL2, Windows)
3. Security hardening
4. Performance / robustness
5. Broadly useful skills
6. New tools (rare — prefer skills/plugins)
7. Docs

## Path selection

| Work | Start doc |
|------|-----------|
| Personal/custom tool, no core change | Plugins guide |
| Built-in core tool | Adding Tools |
| Skill | Creating Skills |
| Inference provider | Adding Providers / model-provider plugin |
| Messaging channel | Adding Platform Adapters |

## Dev environment

Use an authorized source checkout with isolated `HERMES_HOME` and `HERMES_RUNTIME_DIR`. Follow current [PM developer workflow](https://hermes-agent.nousresearch.com/docs/reference/package-management#developer-workflow). Hermes PM pins the development Python (currently 3.14):

```bash
source ./activate
python -m pm.build_env --source . --out .venv --group dev --group test
scripts/run_tests.sh
```

The build destination must not already exist. Use `HERMES_PYTHON` if the independent test environment is outside the checkout. Do not mutate a PM-built environment with raw `pip` or `uv`.

## Code rules

- Profile-safe paths: `get_hermes_home()` / `display_hermes_home()` — never hardcode `~/.hermes`
- Secrets in `.env`; behavioral config in `config.yaml`
- Handlers return JSON strings; no raised errors to the model
- Preserve prompt caching + message alternation
- Cross-platform: gate `SIGKILL`/`setsid`/`killpg`/`fork`; explicit UTF-8; pathlib
- Windows footguns: `scripts/check-windows-footguns.py` when touching I/O, processes, terminals

## Security

- `shlex.quote()` for shell interpolation of untrusted input
- `os.path.realpath()` before path allow/deny checks
- Don't log secrets
- Broad exception catch around tool execution; fail safe

## Before PR

- [ ] Reproduced on current `main`
- [ ] Fixed whole bug class (sibling call sites)
- [ ] Verified premise (not fighting intentional design)
- [ ] `scripts/run_tests.sh` (full or focused) with isolated `HERMES_HOME`
- [ ] For profile-scoped behavior, exercised A→B→A through real imports
- [ ] If dependencies changed, PM lockfile and version bounds updated together
- [ ] Manual `hermes` exercise of the path
- [ ] Cross-platform impact considered
- [ ] Focused single logical change
- [ ] Conventional commit: `fix|feat|docs|test|refactor|chore(scope): …`

## PR body

What / why · how to test · platforms tested · related issues.

## Do not merge (even if polished)

- Speculative hooks with no consumer
- New `HERMES_*` env for non-secrets
- Core tool when skill/plugin/MCP suffices
- Lazy pagination on instructional loaders
- "Security" that kills the feature
- Outbound telemetry without opt-in
- Change-detector tests
- Mid-conversation cache breaks
- Third-party product plugins into core tree
- Plugins that edit core files

## Community

- Discord: discord.gg/NousResearch
- Issues: github.com/NousResearch/hermes-agent/issues
- Security issues: report privately
