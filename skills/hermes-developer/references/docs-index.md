# Hermes Developer Docs Index

Canonical online base: `https://hermes-agent.nousresearch.com/docs/developer-guide/`  
Local base (when installed): `${HERMES_HOME:-$HOME/.hermes}/hermes-agent/website/docs/developer-guide/`  
AI/dev guide: `${HERMES_HOME:-$HOME/.hermes}/hermes-agent/AGENTS.md`

After refresh, see `LAST_REFRESH.md` for commit/date stamp.

## Developer Guide

| Page | URL path | Local file |
|------|----------|------------|
| Contributing | contributing | contributing.md |
| Architecture | architecture | architecture.md |
| Agent Loop | agent-loop | agent-loop.md |
| Prompt Assembly | prompt-assembly | prompt-assembly.md |
| Context Compression & Caching | context-compression-and-caching | context-compression-and-caching.md |
| Session Storage | session-storage | session-storage.md |
| Provider Runtime | provider-runtime | provider-runtime.md |
| Programmatic Integration | programmatic-integration | programmatic-integration.md |
| Adding Tools | adding-tools | adding-tools.md |
| Adding Providers | adding-providers | adding-providers.md |
| Adding Platform Adapters | adding-platform-adapters | adding-platform-adapters.md |
| Plugins | plugins (slug) | plugins/index.md |
| Plugin LLM Access | plugin-llm-access | plugin-llm-access.md |
| Memory Provider Plugin | memory-provider-plugin | memory-provider-plugin.md |
| Context Engine Plugin | context-engine-plugin | context-engine-plugin.md |
| Secret Source Plugin | secret-source-plugin | secret-source-plugin.md |
| Model Provider Plugin | model-provider-plugin | model-provider-plugin.md |
| Image Gen Provider Plugin | image-gen-provider-plugin | image-gen-provider-plugin.md |
| Video Gen Provider Plugin | video-gen-provider-plugin | video-gen-provider-plugin.md |
| Web Search Provider Plugin | web-search-provider-plugin | web-search-provider-plugin.md |
| Browser Provider Plugin | browser-provider-plugin | browser-provider-plugin.md |
| Creating Skills | creating-skills | creating-skills.md |
| Extending the CLI | extending-the-cli | extending-the-cli.md |
| Tools Runtime | tools-runtime | tools-runtime.md |
| Browser Supervisor | browser-supervisor | browser-supervisor.md |
| Gateway Internals | gateway-internals | gateway-internals.md |
| ACP Internals | acp-internals | acp-internals.md |
| Cron Internals | cron-internals | cron-internals.md |
| Trajectory Format | trajectory-format | trajectory-format.md |

Full URL = base + path (e.g. `…/docs/developer-guide/architecture`).

## Reading order (new to codebase)

1. architecture  
2. agent-loop  
3. prompt-assembly  
4. provider-runtime  
5. adding-providers (practical)  
6. tools-runtime  
7. session-storage  
8. gateway-internals  
9. context-compression-and-caching  
10. acp-internals  

## Related non-dev docs

| Topic | Path under docs site |
|-------|----------------------|
| User configuration | /docs/user-guide/configuration |
| Features (plugins, MCP, skills, cron, memory) | /docs/user-guide/features/ |
| Messaging platforms | /docs/user-guide/messaging/ |
| Providers (user) | /docs/integrations/providers |
| Tools reference | /docs/reference/tools-reference |
| Slash commands | /docs/reference/slash-commands |
| CLI commands | /docs/reference/cli-commands |
| Env vars | /docs/reference/environment-variables |

## Load strategy for agents

- Prefer **local markdown** under `website/docs/developer-guide/` when the checkout exists (offline, version-matched to install).
- Prefer **live docs** when validating what users see after `hermes update` or when local tree is dirty/old.
- Prefer **AGENTS.md** for contribution rubric, footprint ladder, and AI-agent working rules.
- Prefer **source** (`run_agent.py`, `tools/registry.py`, …) when docs and code conflict — then patch docs or skill.
