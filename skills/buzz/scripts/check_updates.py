#!/usr/bin/env python3
"""Check whether skills/buzz/SKILL.md has gone stale against upstream block/buzz.

Buzz moves fast. Rather than diffing repo HEAD (which churns constantly and tells
you nothing), this watches only the files each SKILL.md claim actually rests on,
and reports the commit subjects landed on each one since the skill was compiled.

Usage:
    python3 check_updates.py              # has upstream Buzz drifted?
    python3 check_updates.py --repo       # is my copy of this SKILL stale vs its repo?
    python3 check_updates.py --all        # both
    python3 check_updates.py --verbose    # include unchanged files
    python3 check_updates.py --update     # re-pin SHAs (ONLY after repairing SKILL.md)

Exit codes: 0 = current, 1 = drift found, 2 = check could not run.

Stdlib only. Uses GH_TOKEN / GITHUB_TOKEN when present; falls back to
unauthenticated requests (60/hr rate limit, enough for one run).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.github.com"
MANIFEST = Path(__file__).resolve().parent.parent / "watch.json"
# How far back to walk a file's history looking for the pinned commit.
HISTORY_DEPTH = 30


def _get(url: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "buzz-skill-update-check",
    })
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def commits_for_path(repo: str, branch: str, path: str) -> list[dict]:
    url = (f"{API}/repos/{repo}/commits"
           f"?path={urllib.parse.quote(path)}&sha={branch}&per_page={HISTORY_DEPTH}")
    return _get(url)


def probe_absent(repo: str, term: str) -> int | str:
    """Return hit count for a code search, or a reason string if unavailable.

    Never reports a failed probe as a pass: the caller must distinguish
    "searched and found nothing" from "could not search".
    """
    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        return "code search needs GH_TOKEN"
    url = f"{API}/search/code?q={urllib.parse.quote(f'{term} repo:{repo}')}&per_page=1"
    try:
        return int(_get(url).get("total_count", 0))
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            # Code search allows ~10 req/min even when authenticated.
            return "rate limited (code search allows ~10/min) — wait and re-run"
        return f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"network error: {exc}"


def check_distribution(manifest: dict) -> int:
    """Compare local skill files against the copy published in the skills repo.

    Answers a different question from the rest of this script: not "has Buzz
    changed" but "is the copy I am reading out of date with its canonical home".
    Returns 0 in sync, 1 drifted, 2 could not check.
    """
    import hashlib
    d = manifest.get("distribution")
    if not d:
        print("no `distribution` block in watch.json — nothing to compare against")
        return 2
    repo, branch, base = d["repo"], d.get("branch", "main"), d["path"].rstrip("/")
    root = MANIFEST.parent
    print(f"skill distribution — {repo}@{branch} :: {base}")

    drift, errors = [], []
    for rel in d["files"]:
        local = root / rel
        if not local.exists():
            errors.append(f"{rel}: missing locally"); continue
        try:
            meta = _get(f"{API}/repos/{repo}/contents/"
                        f"{urllib.parse.quote(f'{base}/{rel}')}?ref={branch}")
        except urllib.error.HTTPError as exc:
            errors.append(f"{rel}: HTTP {exc.code}" +
                          (" (not published yet)" if exc.code == 404 else "")); continue
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"network error: {exc}", file=sys.stderr); return 2

        # git blob sha, not a content hash — matches what the API reports
        body = local.read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()
        if blob != meta.get("sha"):
            drift.append(rel)

    for e in errors:
        print(f"  ! {e}")
    if drift:
        print(f"\nDRIFT — {len(drift)} file(s) differ from the published copy:")
        for rel in drift:
            print(f"  · {rel}")
        print(f"\n  https://github.com/{repo}/tree/{branch}/{base}")
        print("  If the repo is newer: re-install or copy down.")
        print("  If your local edits are newer: commit and push them up.")
        return 1
    if errors:
        return 2
    print("  in sync with the published copy.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true",
                    help="re-pin SHAs in watch.json (only after repairing SKILL.md)")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="list unchanged files too")
    ap.add_argument("--skip-probes", action="store_true",
                    help="skip the absence probes")
    ap.add_argument("--repo", action="store_true",
                    help="compare this skill against its published copy, and stop")
    ap.add_argument("--all", action="store_true",
                    help="run the upstream-drift check AND the repo comparison")
    args = ap.parse_args()

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"cannot read manifest: {exc}", file=sys.stderr)
        return 2

    if args.repo:
        return check_distribution(manifest)

    repo = manifest["repo"]
    branch = manifest.get("branch", "main")

    print(f"buzz skill staleness check — {repo}@{branch}")
    print(f"skill compiled {manifest['compiled_at']}\n")

    drifted: list[tuple[dict, list[dict]]] = []
    errors: list[str] = []

    for entry in manifest["files"]:
        path, pinned = entry["path"], entry["sha"]
        try:
            commits = commits_for_path(repo, branch, path)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                print("rate limited by the GitHub API — set GH_TOKEN and retry",
                      file=sys.stderr)
                return 2
            errors.append(f"{path}: HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"network error: {exc}", file=sys.stderr)
            return 2

        if not commits:
            errors.append(f"{path}: no commits returned (moved or deleted?)")
            continue

        newest = commits[0]["sha"]
        if newest.startswith(pinned):
            if args.verbose:
                print(f"  ok        {path}")
            continue

        # Collect everything that landed above the pinned commit.
        newer = []
        for c in commits:
            if c["sha"].startswith(pinned):
                break
            newer.append(c)
        entry["_newest"] = newest
        drifted.append((entry, newer))

    # ---- report ----------------------------------------------------------
    if drifted:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        drifted.sort(key=lambda d: order.get(d[0].get("priority", "low"), 9))
        print(f"DRIFT — {len(drifted)} watched file(s) changed:\n")
        for entry, newer in drifted:
            pri = entry.get("priority", "low").upper()
            capped = len(newer) >= HISTORY_DEPTH
            count = f"{len(newer)}+" if capped else str(len(newer))
            print(f"  [{pri}] {entry['path']}  ({count} commit(s))")
            print(f"         repairs: {entry['backs']}")
            for c in newer[:5]:
                subject = c["commit"]["message"].splitlines()[0][:78]
                print(f"           · {c['commit']['committer']['date'][:10]}  {subject}")
            if len(newer) > 5:
                print(f"           · … and {len(newer) - 5} more")
            print(f"         https://github.com/{repo}/commits/{branch}/{entry['path']}")
            print()

    if errors:
        print("could not check:")
        for e in errors:
            print(f"  ! {e}")
        print()

    # ---- absence probes --------------------------------------------------
    probe_failures = []
    if not args.skip_probes:
        terms = manifest.get("absence_probes", {}).get("terms", [])
        skipped_reason = None
        for term in terms:
            hits = probe_absent(repo, term)
            if isinstance(hits, str):
                skipped_reason = hits
                continue
            if hits > 0:
                probe_failures.append((term, hits))
        if skipped_reason:
            print(f"absence probes SKIPPED — {skipped_reason}")
            print("  the 'no loop guard' claim is UNVERIFIED this run.\n")
        elif probe_failures:
            print("ABSENCE PROBE FAILED — Buzz may have grown a coordination layer:")
            for term, hits in probe_failures:
                print(f"  ! '{term}' now returns {hits} hit(s) — rewrite 'What Buzz does not have' and 'If you are comparing'")
            print()
        elif terms:
            print("absence probes: all clear ('What Buzz does not have' still holds)\n")

    # ---- update ----------------------------------------------------------
    if args.update:
        if not drifted:
            print("nothing to re-pin.")
            return 0
        for entry, _ in drifted:
            entry["sha"] = entry.pop("_newest")[:12]
        for entry in manifest["files"]:
            entry.pop("_newest", None)
        manifest["compiled_at"] = date.today().isoformat()
        try:
            manifest["head_at_compile"] = _get(
                f"{API}/repos/{repo}/commits/{branch}")["sha"]
        except Exception:
            pass
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"re-pinned {len(drifted)} file(s); compiled_at = {manifest['compiled_at']}")
        print("now update SKILL.md Provenance to match.")
        return 0

    if args.all:
        print()
        dist_rc = check_distribution(manifest)
    else:
        dist_rc = 0

    if not drifted and not errors and not probe_failures:
        print("SKILL.md is current.")
        return dist_rc or 0

    if drifted or probe_failures:
        print("Repair: re-read each drifted file, fix the sections named above,")
        print("then re-run with --update to re-pin.")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
