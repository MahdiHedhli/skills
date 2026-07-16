# Doc headings snapshot

Generated: 2026-07-16 (finish pass from local tree + content search)
Repo: `/Users/mhedhli/.hermes/hermes-agent`
Commit: `a6d9d1d` (main) — full `a6d9d1d2cf2a72e2c1e60fef973f95b90a18bfd7`

## architecture.md
- title: Architecture
- h2: System Overview · Directory Structure · Data Flow · Recommended Reading Order · Major Subsystems · Design Principles · File Dependency Chain

## agent-loop.md
- title: Agent Loop Internals
- h2: Core Responsibilities · Two Entry Points · API Modes · Turn Lifecycle · Interruptible API Calls · Tool Execution · Callback Surfaces · Budget and Fallback Behavior · Compression and Persistence · Key Source Files · Related Docs

## prompt-assembly.md
- title: Prompt Assembly
- h2: Cached system prompt layers · Customizing platform hints · (ephemeral layers / cache stability — see page)

## context-compression-and-caching.md
- h2: Pluggable Context Engine · Dual Compression System · Configuration · Compression Algorithm · Prompt Caching (Anthropic) · Context Pressure Warnings

## session-storage.md
- title: Session Storage (see page for full H2s)

## provider-runtime.md
- title: Provider Runtime Resolution

## programmatic-integration.md
- title: Programmatic Integration

## contributing.md
- title: Contributing
- h2: Contribution Priorities · Common contribution paths · Development Setup · Code Style · Cross-Platform Compatibility · Security Considerations · Pull Request Process · Reporting Issues · Community · License

## adding-tools.md
- title: Adding Tools
- h2: Overview · Step 1 Create tool file · Step 2 toolset · Async Handlers · task_id · Agent-Loop Intercepted Tools · Setup Wizard · Checklist

## adding-providers.md
- title: Adding Providers
- h2: The mental model · Choose path · File checklist · Fast path API-key · Full path OAuth · Steps 1–10 · OpenAI-compatible checklist · Native checklist · Common pitfalls

## adding-platform-adapters.md
- title: Adding Platform Adapters (see page)

## plugins/index.md
- title: Build a Hermes Plugin
- note: large guide — tools, hooks, skills, data files, interface map

## plugin-llm-access.md
- title: Plugin LLM Access

## memory-provider-plugin.md
- title: Memory Provider Plugins
- h2: Directory Structure · MemoryProvider ABC · Required Methods · Config Schema · Save Config · Entry Point · plugin.yaml · Threading · Profile Isolation · Testing · CLI · Single Provider Rule

## context-engine-plugin.md
- title: Context Engine Plugins

## secret-source-plugin.md
- title: Secret Source Plugins

## model-provider-plugin.md
- title: Model Provider Plugins

## image-gen-provider-plugin.md
- title: Image Generation Provider Plugins
- h2: discovery · directory · ImageGenProvider ABC · plugin.yaml · response format · testing · pip distribute

## video-gen-provider-plugin.md
- title: Video Generation Provider Plugins
- h2: unified surface · discovery · VideoGenProvider ABC · manifest · schema · selection · response · artifacts · testing

## web-search-provider-plugin.md
- title: Web Search Provider Plugins
- h2: discovery · directory · WebSearchProvider ABC · plugin.yaml · response shape · capability flags · wiring · testing · pip

## browser-provider-plugin.md
- title: Browser Provider Plugins

## creating-skills.md
- title: Creating Skills
- h2: Skill vs Tool · Directory Structure · SKILL.md Format · Secure Setup · Guidelines · Where skill lives · Blueprints · Suggested Cron · Publishing · Security Scanning

## extending-the-cli.md
- title: Extending the CLI

## tools-runtime.md
- title: Tools Runtime
- h2: registration model · check_fn · toolset resolution · (environments — see page)

## browser-supervisor.md
- title: Browser CDP Supervisor

## gateway-internals.md
- title: Gateway Internals
- h2: Key Files · Architecture Overview · Message Flow · Authorization · Slash Command Dispatch · Config Sources · Platform Adapters · Delivery Path · Hooks · Memory Provider Integration · Background Maintenance · Process Management

## acp-internals.md
- title: ACP Internals

## cron-internals.md
- title: Cron Internals

## trajectory-format.md
- title: Trajectory format (see page)

## AGENTS.md
- h2:
  - What Hermes Is
  - Contribution Rubric — What We Want / What We Don't
  - Development Environment
  - Project Structure
  - TypeScript Style
  - File Dependency Chain
  - AIAgent Class (run_agent.py)
  - CLI Architecture (cli.py)
  - TUI Architecture (ui-tui + tui_gateway)
  - Adding New Tools
  - Dependency Pinning Policy
  - Adding Configuration
  - Skin/Theme System
  - Plugins
  - Skills
  - Toolsets
  - Delegation (`delegate_task`)
  - Curator (skill lifecycle)
  - Cron (scheduled jobs)
  - Kanban (multi-agent work queue)
  - Important Policies
  - Profiles: Multi-Instance Support
  - Known Pitfalls
  - Testing
