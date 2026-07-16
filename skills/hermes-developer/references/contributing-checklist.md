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

Preferred: standard installer → work in `$HERMES_HOME/hermes-agent`:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
cd "${HERMES_HOME:-$HOME/.hermes}/hermes-agent"
uv pip install -e ".[all,dev]"
# optional: npm install
scripts/run_tests.sh
```

Manual clone: put venv **outside** the source tree (agents can wipe relative `venv/`).

Isolated runs: `scripts/dev-sandbox.sh …`

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
- [ ] `scripts/run_tests.sh` or focused pytest with real `HERMES_HOME` temp
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
