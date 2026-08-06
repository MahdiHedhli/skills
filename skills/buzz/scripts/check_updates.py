#!/usr/bin/env python3
"""Check whether the Buzz skill bundle has gone stale against upstream block/buzz.

Buzz moves fast. Rather than diffing repo HEAD (which churns constantly and tells
you nothing), this watches curated high-signal paths backing named canonical sections
and reports the commit subjects landed on each one since the skill was compiled.

Usage:
    python3 check_updates.py              # has upstream Buzz drifted?
    python3 check_updates.py --repo       # is my copy of this SKILL stale vs its repo?
    python3 check_updates.py --all        # both
    python3 check_updates.py --verbose    # include unchanged files
    python3 check_updates.py --ack PATH --from-sha OLD --reviewed-sha NEW
        --disposition claims-updated --note "what was reviewed and repaired"

Exit codes: 0 = current, 1 = drift found, 2 = check could not run.

Stdlib only. Uses GH_TOKEN / GITHUB_TOKEN when present; falls back to
unauthenticated requests (60/hr rate limit, enough for one run).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import date
from pathlib import Path

API = "https://api.github.com"
MANIFEST = Path(__file__).resolve().parent.parent / "watch.json"
# How far back to walk a file's history looking for the pinned commit.
HISTORY_DEPTH = 30
LOCK_TIMEOUT_SECONDS = 45
REQUIRED_MUTABLE_FILES = ("references/learned-info.md",)


def _lock_path(target: Path) -> Path:
    """Return a stable per-target lock outside the replaceable skill bundle."""
    identity = os.path.normcase(str(target.resolve())).encode("utf-8")
    lock_dir = Path(tempfile.gettempdir()) / "buzz-skill-locks"
    lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return lock_dir / f"{hashlib.sha256(identity).hexdigest()}.lock"


@contextmanager
def exclusive_file_lock(target: Path):
    """Hold a portable inter-process lock while updating *target*.

    The stable sidecar lives in the system temporary directory because locking the
    target itself would stop protecting writers after ``os.replace`` swaps in a new
    inode. The sidecar is intentionally retained for reuse.
    """
    lock_path = _lock_path(target)
    handle = lock_path.open("a+b")
    locked = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()

        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"timed out locking {target}")
                    time.sleep(0.05)
        else:
            import fcntl

            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"timed out locking {target}")
                    time.sleep(0.05)

        yield
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


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
    d = manifest.get("distribution")
    if not d:
        print("no `distribution` block in watch.json — nothing to compare against")
        return 2
    repo, branch, base = d["repo"], d.get("branch", "main"), d["path"].rstrip("/")
    root = MANIFEST.parent
    print(f"skill distribution — {repo}@{branch} :: {base}")

    drift, errors = [], []
    for rel in d["files"]:
        if rel in REQUIRED_MUTABLE_FILES:
            # Never compare mutable local knowledge by content, even if an older
            # or hand-edited manifest accidentally lists it as immutable.
            continue
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

    # The learning ledger is mutable local state, so require both bundle copies to
    # contain it without comparing their contents or blob hashes.
    for rel in REQUIRED_MUTABLE_FILES:
        local = root / rel
        if not local.is_file():
            errors.append(f"{rel}: required mutable file missing locally")
            continue
        try:
            _get(
                f"{API}/repos/{repo}/contents/"
                f"{urllib.parse.quote(f'{base}/{rel}')}?ref={branch}"
            )
        except urllib.error.HTTPError as exc:
            errors.append(
                f"{rel}: required mutable file HTTP {exc.code}"
                + (" (not published yet)" if exc.code == 404 else "")
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"network error: {exc}", file=sys.stderr)
            return 2

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


def _write_manifest(manifest: dict) -> None:
    """Atomically replace watch.json while the caller holds its stable lock."""
    body = json.dumps(manifest, indent=2) + "\n"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=MANIFEST.parent, delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, MANIFEST.stat().st_mode)
        os.replace(temp_path, MANIFEST)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def acknowledge_path(args: argparse.Namespace) -> int:
    """Advance exactly one pin after an agent reviewed the current file revision.

    This is deliberately compare-and-swap: a stale maintenance turn cannot bless a
    newer revision it did not review, and one acknowledgement cannot hide unrelated
    drift elsewhere in the skill.
    """
    required = {
        "--from-sha": args.from_sha,
        "--reviewed-sha": args.reviewed_sha,
        "--disposition": args.disposition,
        "--note": args.note,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        print(f"ack requires {', '.join(missing)}", file=sys.stderr)
        return 2
    if len(args.from_sha) < 12 or len(args.reviewed_sha) < 12:
        print("ack SHAs must contain at least 12 hexadecimal characters", file=sys.stderr)
        return 2
    try:
        int(args.from_sha, 16)
        int(args.reviewed_sha, 16)
    except ValueError:
        print("ack SHAs must be hexadecimal", file=sys.stderr)
        return 2
    note = " ".join(args.note.split())
    if len(note) < 12:
        print("ack note must say what was reviewed (at least 12 characters)", file=sys.stderr)
        return 2

    try:
        with exclusive_file_lock(MANIFEST):
            # Re-read after acquiring the lock. Another maintenance process may
            # have advanced this or another path while this process was waiting.
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            matches = [
                entry for entry in manifest["files"] if entry["path"] == args.ack
            ]
            if len(matches) != 1:
                print(f"ack path is not watched exactly once: {args.ack}", file=sys.stderr)
                return 2
            entry = matches[0]
            if entry["sha"] != args.from_sha[:12]:
                print(
                    f"compare-and-swap failed: manifest pins {entry['sha']}, "
                    f"not {args.from_sha[:12]}",
                    file=sys.stderr,
                )
                return 2

            repo = manifest["repo"]
            branch = manifest.get("branch", "main")
            try:
                commits = commits_for_path(repo, branch, entry["path"])
            except urllib.error.HTTPError as exc:
                print(f"cannot verify reviewed revision: HTTP {exc.code}", file=sys.stderr)
                return 2
            except (urllib.error.URLError, TimeoutError) as exc:
                print(f"cannot verify reviewed revision: {exc}", file=sys.stderr)
                return 2
            if not commits:
                print("cannot verify reviewed revision: no commits returned", file=sys.stderr)
                return 2
            latest = commits[0]["sha"]
            if not latest.startswith(args.reviewed_sha):
                print(
                    "compare-and-swap failed: upstream moved after review; "
                    f"latest is {latest[:12]}, reviewed {args.reviewed_sha[:12]}",
                    file=sys.stderr,
                )
                return 2

            old_pin = entry["sha"]
            entry["sha"] = latest[:12]
            manifest.setdefault("reviews", []).append(
                {
                    "date": date.today().isoformat(),
                    "path": entry["path"],
                    "from": old_pin,
                    "to": latest[:12],
                    "disposition": args.disposition,
                    "note": note,
                }
            )
            _write_manifest(manifest)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot update manifest: {exc}", file=sys.stderr)
        return 2

    print(
        f"acknowledged {entry['path']}: {old_pin} -> {latest[:12]} "
        f"({args.disposition})"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true",
                    help="disabled unsafe bulk re-pin; use --ack for one reviewed path")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="list unchanged files too")
    ap.add_argument("--skip-probes", action="store_true",
                    help="skip the absence probes")
    ap.add_argument("--repo", action="store_true",
                    help="compare this skill against its published copy, and stop")
    ap.add_argument("--all", action="store_true",
                    help="run the upstream-drift check AND the repo comparison")
    ap.add_argument("--ack", metavar="PATH",
                    help="advance one watched path after reviewing its current revision")
    ap.add_argument("--from-sha", help="current 12-character manifest pin")
    ap.add_argument("--reviewed-sha", help="current upstream revision actually reviewed")
    ap.add_argument(
        "--disposition",
        choices=("claims-updated", "no-relevant-change"),
        help="whether canonical skill claims required edits",
    )
    ap.add_argument("--note", help="concise evidence/review note stored in watch.json")
    args = ap.parse_args()

    if args.update:
        print(
            "--update is disabled because bulk re-pinning can hide unreviewed drift; "
            "use --ack for one reviewed path at a time",
            file=sys.stderr,
        )
        return 2

    if args.ack:
        return acknowledge_path(args)

    stray_ack_args = (args.from_sha, args.reviewed_sha, args.disposition, args.note)
    if any(stray_ack_args):
        print("--from-sha/--reviewed-sha/--disposition/--note require --ack", file=sys.stderr)
        return 2

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
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

    if args.all:
        print()
        dist_rc = check_distribution(manifest)
    else:
        dist_rc = 0

    if not drifted and not errors and not probe_failures:
        print("Watched Buzz claims are current.")
        return dist_rc or 0

    if drifted or probe_failures:
        print("Repair: re-read each drifted file, fix the sections named above,")
        print("then acknowledge each reviewed path with the compare-and-swap --ack command.")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
