# Hermes skills

Installable [Hermes](https://nousresearch.com/) skills. Tap this repo, then browse / install:

```bash
hermes skills tap add MahdiHedhli/skills
hermes skills search scope-first
hermes skills install MahdiHedhli/skills/scope-first
hermes skills install MahdiHedhli/skills/neckbeard
```

## scope-first

Plan-first discipline for builds. Before delegating or writing code, the agent uses the
`clarify` tool to settle the **target directory**, approach, and v1 scope *interactively*
(one decision at a time, with buttons), then builds. Bypass with “yolo”.

## neckbeard

<img src="skills/neckbeard/neckbeard.jpg" align="right" width="220" alt="Neckbeard mascot — doesn't write less code, writes the correct code" />

Minimalism ruleset for code generation. Climb the ladder (YAGNI → stdlib → platform →
installed dep → one line → minimum that works) while **never pruning the protected set**
(observability, audit logging, idempotency, retries, input validation…). Lazy, not
negligent. Vendored from the Ponytail ruleset (MIT) and renamed.

<br clear="right" />

---

Both skills ship with **[HermesUltraCode](https://github.com/MahdiHedhli/HermesUltraCode)** —
a neutral, *different-lab* **pre-dispatch gate** that vets every Hermes `delegate_task`
(tighten-only, fail-closed, audited), plus a live multi-agent dashboard.
