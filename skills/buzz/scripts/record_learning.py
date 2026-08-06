#!/usr/bin/env python3
"""Append a deduplicated, evidence-backed record to the Buzz learning channel."""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHANNEL = SKILL_ROOT / "references" / "learned-info.md"
LOCK_TIMEOUT_SECONDS = 45
HEADER = """# Buzz learned info

This is the skill's durable learning channel. It stores evidence-backed discoveries
that may be useful across sessions, including operational observations that are too
new or narrow for the canonical guidance.

## Rules

- Search this file before investigating a matching symptom or subsystem.
- Record reusable facts, not a transcript of the task that exposed them.
- Include a source and concrete evidence. Label inference honestly.
- Never record secrets, private keys, access tokens, personal data, or private relay
  content.
- Keep entries after promotion or rejection so the evidence trail remains intact.
- Promote a verified fact into `SKILL.md` or the expert reference when it changes
  canonical guidance, then set the entry status to `promoted` and name the target.

## Entries

<!-- Append records below with scripts/record_learning.py. -->
"""


def one_line(value: str) -> str:
    """Normalize user input into a safe, compact Markdown field."""
    return " ".join(value.split())


def make_record(args: argparse.Namespace) -> tuple[str, str]:
    fields = [
        one_line(args.area),
        one_line(args.title),
        one_line(args.finding),
        *[one_line(source) for source in args.source],
    ]
    record_id = hashlib.sha256("\0".join(fields).encode("utf-8")).hexdigest()[:12]
    marker = f"<!-- buzz-learning:{record_id} -->"
    sources = "; ".join(one_line(source) for source in args.source)
    record = f"""
{marker}
### {args.recorded_at} — {one_line(args.title)}

- ID: `{record_id}`
- Area: {one_line(args.area)}
- Status: {args.status}
- Confidence: {args.confidence}
- Source: {sources}
- Evidence: {one_line(args.evidence)}
- Finding: {one_line(args.finding)}
- Canonical target: {one_line(args.target)}
"""
    return record_id, record


def _lock_path(target: Path) -> Path:
    """Return a stable per-target lock outside the replaceable skill bundle."""
    identity = os.path.normcase(str(target.resolve())).encode("utf-8")
    lock_dir = Path(tempfile.gettempdir()) / "buzz-skill-locks"
    lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return lock_dir / f"{hashlib.sha256(identity).hexdigest()}.lock"


@contextmanager
def exclusive_file_lock(target: Path):
    """Hold a portable inter-process lock across read, dedupe, and replace."""
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


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else None
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp_path, mode)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area", required=True, help="Subsystem or topic")
    parser.add_argument("--title", required=True, help="Short searchable title")
    parser.add_argument("--finding", required=True, help="Reusable fact learned")
    parser.add_argument(
        "--source", required=True, action="append", help="URL, file, issue, or command"
    )
    parser.add_argument("--evidence", required=True, help="What was read or observed")
    parser.add_argument(
        "--confidence",
        choices=("observed", "source-verified", "inferred"),
        default="source-verified",
    )
    parser.add_argument(
        "--status",
        choices=("candidate", "verified", "promoted", "rejected"),
        default="candidate",
    )
    parser.add_argument("--target", default="unassigned", help="Canonical section")
    parser.add_argument(
        "--date", dest="recorded_at", default=date.today().isoformat(), help="YYYY-MM-DD"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    record_id, record = make_record(args)
    if args.dry_run:
        print(record.lstrip())
        return 0

    try:
        DEFAULT_CHANNEL.parent.mkdir(parents=True, exist_ok=True)
        with exclusive_file_lock(DEFAULT_CHANNEL):
            # Re-read under the lock so concurrent writers cannot overwrite one
            # another or append the same deterministic record twice.
            existing = (
                DEFAULT_CHANNEL.read_text(encoding="utf-8")
                if DEFAULT_CHANNEL.exists()
                else HEADER
            )
            marker = f"<!-- buzz-learning:{record_id} -->"
            if marker in existing:
                print(f"learning {record_id} already recorded")
                return 0
            atomic_write(DEFAULT_CHANNEL, existing.rstrip() + "\n" + record)
    except OSError as exc:
        parser.error(f"cannot update {DEFAULT_CHANNEL}: {exc}")
    print(f"recorded learning {record_id} in {DEFAULT_CHANNEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
