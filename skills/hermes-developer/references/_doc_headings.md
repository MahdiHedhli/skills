# Doc headings snapshot

Generated: 2026-09-29T00:18:24Z
Source: `https://github.com/NousResearch/hermes-agent.git`
Commit: `81f481b2db39e9c3e3df8cbb063931746263eca2` (main) — fix(agent): carry a custom provider's extra_body into TUI/Desktop agents and aux calls

## acp-internals.md
- title: ACP Internals
- bytes: 6232
- h2:
  - Boot flow
  - Major components
  - Session lifecycle
  - Provider/auth behavior
  - Working directory binding
  - Duplicate same-name tool calls
  - Approval callback restoration
  - Current limitations
  - Related files

## adding-platform-adapters.md
- title: Adding a Platform Adapter
- bytes: 36553
- h2:
  - Architecture Overview
  - Plugin Path (Recommended)
  - Standalone send-path extensions
  - Env-Driven Auto-Configuration
  - YAML→env Config Bridge
  - Cron Delivery
  - Surfacing Env Vars in `hermes config`
  - Platform-Specific Slow-LLM UX
  - Step-by-Step Checklist (Built-in Path)
  - Parity Audit
  - Common Patterns
  - Reference Implementations

## adding-providers.md
- title: Adding Providers
- bytes: 18059
- h2:
  - The mental model
  - Choose the implementation path first
  - File checklist
  - Fast path: Simple API-key providers
  - Full path: OAuth and complex providers
  - Step 1: Pick one canonical provider id
  - Step 2: Add auth metadata in `hermes_cli/auth.py`
  - Step 3: Add model catalog and aliases in `hermes_cli/models.py`
  - Step 4: Resolve runtime data in `hermes_cli/runtime_provider.py`
  - Step 5: Wire the CLI in `hermes_cli/main.py`
  - Step 6: Keep auxiliary calls working
  - Step 7: If the provider is native, add an adapter and `run_agent.py` support

## adding-tools.md
- title: Adding Tools
- bytes: 6704
- h2:
  - Overview
  - Step 1: Create the Built-in Tool File
  - Step 2: Add the Built-in Tool to a Toolset
  - ~~Step 3: Add Discovery Import~~ (No longer needed)
  - Async Handlers
  - Handlers That Need task_id
  - Agent-Loop Intercepted Tools
  - Optional: Setup Wizard Integration
  - Checklist

## agent-loop.md
- title: Agent Loop Internals
- bytes: 11537
- h2:
  - Core Responsibilities
  - Two Entry Points
  - API Modes
  - Turn Lifecycle
  - Interruptible API Calls
  - Tool Execution
  - Callback Surfaces
  - Budget and Fallback Behavior
  - Compression and Persistence
  - Key Source Files
  - Related Docs

## architecture.md
- title: Architecture
- bytes: 16760
- h2:
  - System Overview
  - Directory Structure
  - Data Flow
  - Recommended Reading Order
  - Major Subsystems
  - Design Principles
  - File Dependency Chain

## billing-lifecycle.md
- title: Billing Lifecycle (TUI)
- bytes: 17513
- h2:
  - 1. `billing.state` shapes → render
  - 2. Refusal codes (`renderBillingError`, in code order)
  - 3. Charge settlement outcomes (`pollCharge` / `renderChargeFailed`)
  - 4. Subscription preview / pending-change / upgrade outcomes
  - Text-mode (CLI) parity
  - Forward compatibility

## browser-provider-plugin.md
- title: Browser Provider Plugins
- bytes: 6852
- h2:
  - How it fits together
  - Discovery
  - Directory structure
  - The BrowserProvider ABC
  - Users configure it
  - Reference implementations
  - Checklist

## browser-supervisor.md
- title: Browser CDP Supervisor
- bytes: 9576
- h2:
  - Backend support
  - Architecture
  - Agent surface
  - Cross-origin iframe interaction
  - File layout
  - Non-goals
  - Testing

## chronos-managed-cron-contract.md
- title: Chronos Managed-Cron Contract
- bytes: 12462
- h2:
  - Trust model (read this first)
  - Endpoint 1 — `POST /api/agent-cron/provision`  (agent → NAS)
  - Endpoint 2 — `POST /api/agent-cron/cancel`  (agent → NAS)
  - Endpoint 3 — `POST /api/agent-cron/relay`  (scheduler → NAS, the fire relay)
  - Inbound `POST /api/cron/fire`  (NAS → agent) — agent side, already implemented
  - At-most-once & re-arm semantics
  - Reconcile (self-healing)
  - Config (agent side)
  - Escape hatch (not default)

## cli-internals.md
- title: CLI Internals
- bytes: 5583
- h2:
  - Update pipeline
  - Process identity: never infer it from argv substrings
  - Skin engine — what skins customize
  - Profiles: multi-instance support

## codebase-ownership.md
- title: Codebase Ownership Map
- bytes: 3322

## completion-backlog-delivery.md
- title: Background completion backlogs
- bytes: 3039
- h2:
  - Consumers and ownership
  - Local validation and its limits

## context-compression-and-caching.md
- title: Context Compression and Caching
- bytes: 43039
- h2:
  - Bedrock context window cache
  - Pluggable Context Engine
  - Dual Compression System
  - Configuration
  - Compression Algorithm
  - Goal
  - Constraints & Preferences
  - Progress
  - Key Decisions
  - Relevant Files
  - Next Steps
  - Critical Context

## context-engine-plugin.md
- title: Context Engine Plugins
- bytes: 20317
- h2:
  - How it works
  - Directory structure
  - The ContextEngine ABC
  - Per-turn context selection and observation
  - Engine tools
  - Registration
  - Lifecycle
  - Configuration
  - Testing
  - Thread safety
  - See also

## contributing.md
- title: Contributing
- bytes: 14778
- h2:
  - Contribution Priorities
  - Common contribution paths
  - Development Setup
  - Code Style
  - Cross-Platform Compatibility
  - Security Considerations
  - Pull Request Process
  - Reporting Issues
  - Community
  - License

## creating-skills.md
- title: Creating Skills
- bytes: 20125
- h2:
  - Should it be a Skill or a Tool?
  - Skill Directory Structure
  - SKILL.md Format
  - When to Use
  - Quick Reference
  - Procedure
  - Pitfalls
  - Verification
  - Secure Setup on Load
  - Skill Guidelines
  - Where Should the Skill Live?
  - Blueprints: skills that are also automations

## cron-internals.md
- title: Cron Internals
- bytes: 25317
- h2:
  - Key Files
  - Scheduling Model
  - Job Storage
  - Scheduler Runtime
  - Skill-Backed Jobs
  - Delivery Model
  - Recursion Guard
  - Locking
  - CLI Interface
  - Related Docs

## desktop-plugin-sdk.md
- title: Desktop Plugin SDK (@hermes/plugin-sdk)
- bytes: 86079
- h2:
  - Mental model
  - Two delivery modes
  - Quick start — your first plugin
  - The plugin contract
  - Contribution areas — the cookbook
  - Host API
  - Data layer — React Query + nanostores
  - The UI kit and theming
  - A backend for your plugin
  - Settings, enable state, and storage
  - Bundled plugins
  - Security model

## egress-internals.md
- title: Egress proxy internals
- bytes: 20489
- h2:
  - Module layout
  - Lifecycle
  - Security invariants
  - Extension points
  - Testing
  - See also

## extending-the-cli.md
- title: Extending the CLI
- bytes: 7412
- h2:
  - Extension points
  - Quick start: a wrapper CLI
  - Hook reference
  - Layout diagram
  - Tips

## gateway-internals.md
- title: Gateway Internals
- bytes: 22654
- h2:
  - Key Files
  - Architecture Overview
  - Message Flow
  - Authorization
  - Slash Command Dispatch
  - Config Sources
  - Platform Adapters
  - Delivery Path
  - Hooks
  - Memory Provider Integration
  - Background Maintenance
  - Process Management

## gateway-monitoring.md
- title: Gateway Monitoring
- bytes: 15326
- h2:
  - What gets exported
  - Enabling
  - Collecting into DataDog
  - Generic fleet queries and alerts
  - Release-validation scenarios
  - Local smoke test (no Docker)
  - Maintaining and extending this plane
  - Boundaries and roadmap

## gateway-session-lifecycle.md
- title: Gateway Session Lifecycle
- bytes: 35054
- h2:
  - Overview
  - 1. SessionSource — Message Origin Descriptor
  - 2. SessionEntry — Active Session Record
  - 3. SessionStore — Storage and Operations
  - 4. SessionKey Generation Rules
  - 5. Multi-User Isolation Strategy
  - 6. Explicit Conversation Boundaries
  - 7. Restart Recovery Flow
  - 8. Message Queuing Flow
  - 9. Session Context Injection
  - 10. Background Housekeeping
  - 11. Agent Cache

## image-gen-provider-plugin.md
- title: Image Generation Provider Plugins
- bytes: 12919
- h2:
  - How discovery works
  - Directory structure
  - The ImageGenProvider ABC
  - plugin.yaml
  - ABC reference
  - Response format
  - Handling base64 vs URL output
  - User overrides
  - Testing
  - Reference implementations
  - Distribute via pip
  - Related pages

## macos-bundle-updates.md
- title: macOS bundle updates
- bytes: 4885
- h2:
  - Feed contract
  - Client lifecycle
  - Release environment
  - Verification limits

## memory-provider-plugin.md
- title: Memory Provider Plugins
- bytes: 25093
- h2:
  - Installation Layouts
  - The MemoryProvider ABC
  - Required Methods
  - Pre-Compress Checkpoints (fail-closed)
  - Setup UX — what a standalone provider keeps
  - Config Schema
  - Save Config
  - Plugin Entry Point
  - plugin.yaml
  - Threading Contract
  - Profile Isolation
  - Testing

## micro-compaction.md
- title: Micro-compaction
- bytes: 20088
- h2:
  - What it does
  - Your messages are never compacted
  - What it never touches
  - How it works
  - Interaction with batch compaction
  - Configuration
  - Prompt caching — the cost you are opting into
  - Choosing a compression model
  - Measuring it
  - Failure behaviour

## middleware.md
- title: Middleware
- bytes: 9855
- h2:
  - Contract
  - Execution Order
  - Enablement
  - Generic Plugin Examples
  - Safety Notes

## model-provider-plugin.md
- title: Model Provider Plugins
- bytes: 41172
- h2:
  - How discovery works
  - Directory structure
  - Minimal example — a simple API-key provider
  - ProviderProfile fields
  - Declaring model capabilities
  - Overridable hooks
  - Account usage
  - External-process (ACP) providers
  - Hook reference examples
  - User overrides — replace a built-in without editing the repo
  - api_mode selection
  - Auth types

## multiplexing-gateway.md
- title: Multiplexing Gateway Internals
- bytes: 19731
- h2:
  - Overview
  - The mode flag
  - Scope composition
  - Workstream A: context-local secret scope
  - The HERMES_HOME override
  - Inbound routing
  - Serving selected profiles
  - Per-profile persistence
  - Per-bot session lanes
  - Intake vs delivery: which bot acts on an event
  - Control plane
  - Failure modes

## observer-hooks.md
- title: Observer Hooks
- bytes: 12943
- h2:
  - Contract
  - Correlation IDs
  - Event Families
  - Payload Safety
  - Performance
  - Writing An Observer Plugin
  - Existing Consumers

## onboarding-recommendations.md
- title: Onboarding recommendations
- bytes: 8207
- h2:
  - What takes priority
  - Catalog metadata
  - Discovery and scope
  - Recommendation and execution boundaries
  - Compatibility with the connection-operation work
  - Verification boundaries

## plugin-llm-access.md
- title: Plugin LLM Access
- bytes: 19888
- h2:
  - The smallest possible call
  - A more complete chat example
  - Structured output
  - What this lane gives you
  - Quick start
  - When to use which
  - API surface
  - Trust gate
  - What the host owns
  - What the plugin owns
  - Where this fits in the plugin surface
  - Reference

## plugins/application-declarations.md
- title: Application declarations
- bytes: 5333
- h2:
  - `app` — how to find the application on each OS
  - `requires` — what the server needs before it is offered
  - Availability: the one evaluation every reader uses
  - The two gates

## plugins/index.md
- title: Build a Hermes Plugin
- bytes: 97486
- h2:
  - Portable Agent Plugins v1 packages
  - Native plugin compatibility contract
  - What you're building
  - Step 1: Create the plugin directory
  - Step 2: Write the manifest
  - Step 3: Write the tool schemas
  - Step 4: Write the tool handlers
  - Step 5: Write the registration
  - Step 6: Test it
  - Your plugin's final structure
  - What else can plugins do?
  - Specialized plugin types

## pm-audit-status.md
- title: PM audit remediation status
- bytes: 13258
- h2:
  - Runtime repairs after the documentation audit
  - Implemented repairs
  - Closure implementation
  - Verified execution
  - Merge-ready closeout
  - Non-E2E closeout
  - Bundle acceptance (separate workstream)
  - Remaining gates

## programmatic-integration.md
- title: Programmatic Integration
- bytes: 19003
- h2:
  - ACP (Agent Client Protocol)
  - TUI Gateway JSON-RPC
  - OpenAI-Compatible API Server
  - Which one should I use?
  - Model hot-swapping
  - A note on `--mode rpc`

## prompt-assembly.md
- title: Prompt Assembly
- bytes: 15808
- h2:
  - Cached system prompt layers
  - Persistent Memory
  - User Profile
  - Skills (mandatory)
  - AGENTS.md
  - Customizing platform hints
  - How SOUL.md appears in the prompt
  - How context files are injected
  - API-call-time-only layers
  - Memory snapshots
  - Context files
  - Skills index

## provider-runtime.md
- title: Provider Runtime Resolution
- bytes: 10851
- h2:
  - Chat-completions reasoning shapes
  - Resolution precedence
  - Providers
  - Output of runtime resolution
  - Why this matters
  - AI Gateway
  - OpenRouter, AI Gateway, and custom OpenAI-compatible base URLs
  - Native Anthropic path
  - OpenAI Codex path
  - Auxiliary model routing
  - Fallback models
  - Related docs

## relay-connector-contract.md
- title: Relay ↔ Connector Contract
- bytes: 52024
- h2:
  - 1. Handshake
  - 2. CapabilityDescriptor (handshake payload)
  - 3. Inbound: `MessageEvent` envelope
  - 4. Outbound: action set
  - 5. Interrupt (`/stop`) routing
  - 6. Trust boundary & signed-body handling (A2)
  - 7. Per-instance delivery & the management plane (Phase 6)
  - 8. Gateway-side platform behavior controls (enterprise)
  - 9. Versioning policy

## relay-shared-metrics.md
- title: Relay Shared Metrics
- bytes: 60733
- h2:
  - Runtime Dependency and Data Boundary
  - Session-Span Segmentation for Continuous Sessions
  - Working-Directory Scope Data
  - Process-Wide Plugin Policy and Profile Isolation
  - Current Slices
  - Smoke Test
  - Appendix A: Remote Exporter Decisions (Phase 2)

## secret-source-plugin.md
- title: Secret Source Plugins
- bytes: 10783
- h2:
  - First-process bootstrap timing
  - What the framework owns vs. what you own
  - Directory structure
  - The SecretSource ABC
  - Subprocess safety: use `run_secret_cli()`
  - Registering
  - Users configure it like any other source
  - Validate with the conformance kit
  - ErrorKind reference

## session-storage.md
- title: Session Storage
- bytes: 27772
- h2:
  - Hermes home and profile isolation
  - Codex app-server input ownership
  - Gateway exception-path input ownership
  - Architecture Overview
  - SQLite Schema
  - Schema Version and Migrations
  - Write Contention Handling
  - Common Operations
  - Full-Text Search
  - Session Lineage
  - Export and Cleanup
  - Database Location

## shared-bundle-builds.md
- title: Shared bundle builds
- bytes: 24791
- h2:
  - Providers, products, and distributions
  - Build and packaging entrypoints
  - Shared agent and launcher contract
  - Independent PM runtime
  - Distribution boundaries and output paths
  - Public artifact handoffs
  - Cache ownership
  - Pinned binary inputs
  - Verification boundary

## source-update-completion.md
- title: Source update completion ownership
- bytes: 5382
- h2:
  - Phase seam
  - New-code owner
  - Parent lifecycle and failures
  - Historical surface
  - Verification

## stable-releases.md
- title: Stable release admission and promotion
- bytes: 27273
- h2:
  - Order
  - Run, publish, or abandon a stable release
  - Failure and recovery
  - Tag namespaces and receipts
  - Canary and one-off desktop identities
  - Dynamic channels in R2
  - Signed-package baseline
  - Explicit exclusions and policy
  - Implementation ownership

## state-db-recovery.md
- title: State DB Recovery
- bytes: 5025
- h2:
  - Live behavior when FTS is corrupt
  - Live behavior when the file itself is corrupt
  - Explicit repair

## streaming-tts.md
- title: Streaming TTS Internals
- bytes: 4674
- h2:
  - Architecture
  - How to pick a provider
  - Capability matrix
  - Adding a new streaming provider
  - Gateway streaming (platform adapters)

## subagent-lifecycle-api.md
- title: Public Subagent Lifecycle API
- bytes: 2947

## terminal-environment-plugin.md
- title: Terminal Environment Provider Plugins
- bytes: 5517
- h2:
  - What a provider controls
  - Minimal provider
  - Rules
  - Environment object contract
  - Session isolation semantics

## tools-runtime.md
- title: Tools Runtime
- bytes: 12084
- h2:
  - Tool registration model
  - Tool availability checking (`check_fn`)
  - Toolset resolution
  - Dispatch
  - The DANGEROUS_PATTERNS approval flow
  - Terminal/runtime environments
  - Concurrency
  - Related docs

## trajectory-format.md
- title: Trajectory Format
- bytes: 8413
- h2:
  - File Naming Convention
  - JSONL Entry Format
  - Conversations Array (ShareGPT Format)
  - Normalization Rules
  - Loading Trajectories
  - Controlling Trajectory Saving

## video-gen-provider-plugin.md
- title: Video Generation Provider Plugins
- bytes: 9366
- h2:
  - The unified surface (one tool, two modalities)
  - How discovery works
  - Directory structure
  - The VideoGenProvider ABC
  - The plugin manifest
  - The `video_generate` schema
  - Model families and endpoint routing (the FAL pattern)
  - Selection precedence
  - Response shape
  - Where to save artifacts
  - Testing

## web-search-provider-plugin.md
- title: Web Search Provider Plugins
- bytes: 11544
- h2:
  - How discovery works
  - Directory structure
  - The WebSearchProvider ABC
  - plugin.yaml
  - ABC reference
  - Response shape
  - Capability flags
  - How Hermes wires it into the tools
  - Lazy-installing optional dependencies
  - Reference implementations
  - Distribute via pip
  - Related pages

## worktree-ui-dev.md
- title: TUI & Desktop from Worktrees
- bytes: 9470
- h2:
  - The deps-sharing model
  - `htui` — TUI from the worktree
  - `hgui` — desktop app from the worktree
  - Shared helpers
  - See also

## AGENTS.md
- bytes: 36537
- h2:
  - What Hermes Is
  - Contribution Rubric — What We Want / What We Don't
  - Development Environment
  - Project Structure
  - Code Shape Rules (all languages)
  - Dependency Pinning Policy
  - Commits, Merges, PRs
  - Testing (applies everywhere)
  - Routing Table — working in X → read X/AGENTS.md
