# Last refresh

- **status:** ok (manual finish pass — content derived from local checkout + docs already loaded in session)
- **refreshed_at:** 2026-07-16T00:00:00Z
- **repo:** `/Users/mhedhli/.hermes/hermes-agent`
- **git_commit:** `a6d9d1d` (full: `a6d9d1d2cf2a72e2c1e60fef973f95b90a18bfd7`)
- **git_branch:** `main`
- **developer_guide_pages_found:** 29/29 tracked md pages (see docs-index; excludes `_category_.json`)
- **missing_pages:** (none)
- **AGENTS.md:** present (major H2s snapshotted in `_doc_headings.md`)
- **headings_snapshot:** `references/_doc_headings.md`

## Skill completeness (this finish pass)

| Artifact | Status |
|----------|--------|
| `SKILL.md` | complete v1.1.0 |
| `references/docs-index.md` | complete |
| `references/extension-map.md` | complete |
| `references/architecture-snapshot.md` | complete |
| `references/contributing-checklist.md` | complete |
| `references/workflows.md` | complete |
| `scripts/refresh_from_docs.py` | complete |
| `scripts/refresh_from_docs.sh` | complete |
| Cross-link from `hermes-agent` skill | done |

## Agent follow-up on next Hermes update

1. Run `python ${HERMES_SKILL_DIR}/scripts/refresh_from_docs.py`
2. Diff `_doc_headings.md`
3. Patch SKILL / references if ladders or file maps drift
4. Optionally refresh related skill `hermes-agent` for user-facing CLI/config changes

## Live docs

https://hermes-agent.nousresearch.com/docs/developer-guide/
