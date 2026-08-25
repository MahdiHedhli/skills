# Review Packet Reference

## Challenger packet

Include:

- exact reviewed head and tree
- authority manifest
- active graph frontier
- readiness-critical claims
- implementation diff from prior reviewed head
- transitive dependency SHAs
- test and mutation index
- prior challenges and support dispositions
- exact attack questions

The challenger returns structured challenge rows.

## Arbiter packet

Include:

- exact reviewed head and tree
- final authority manifest
- claim ledger
- challenge ledger
- support ledger
- node receipts
- exact-head CI
- qualification evidence
- changed claims since prior cycle
- invalidation map
- final safety state

The arbiter returns one verdict per readiness-critical claim plus one global verdict.

## Packet discipline

- Do not repeat the whole project history.
- Do not substitute prose for exact paths and SHAs.
- Do not hide failed review attempts.
- Do not delete superseded findings.
- Distinguish implementation head from evidence head.
- Distinguish current authority from historical reconstruction.
