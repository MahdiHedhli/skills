#!/usr/bin/env python3
"""Refresh hermes-developer skill references from local Hermes checkout docs.

Prefer the version-matched tree under $HERMES_HOME/hermes-agent. Writes:
  - references/LAST_REFRESH.md
  - references/_doc_headings.md (title + first H2s per page for drift detection)

Does NOT rewrite SKILL.md — agent should patch that after reviewing diffs.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def find_repo() -> Path | None:
    candidates = [
        hermes_home() / "hermes-agent",
        Path.cwd() / "hermes-agent",
        Path.cwd(),
    ]
    env = os.environ.get("HERMES_AGENT_REPO")
    if env:
        candidates.insert(0, Path(env).expanduser())
    for c in candidates:
        if (c / "website/docs/developer-guide").is_dir() and (c / "AGENTS.md").is_file():
            return c
        if (c / "docs/developer-guide").is_dir():  # alternate layout
            return c
    return None


def git_info(repo: Path) -> dict:
    info = {"commit": "unknown", "branch": "unknown", "subject": "", "date": "", "remote": "unknown"}
    try:
        def run(*args: str) -> str:
            return subprocess.check_output(
                ["git", "-C", str(repo), *args],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()

        info["commit"] = run("rev-parse", "HEAD")
        info["branch"] = run("rev-parse", "--abbrev-ref", "HEAD")
        info["subject"] = run("log", "-1", "--pretty=%s")
        info["date"] = run("log", "-1", "--pretty=%cI")
        info["remote"] = run("remote", "get-url", "origin")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return info


def extract_heading_meta(text: str) -> tuple[str, list[str]]:
    title = ""
    h2: list[str] = []
    # frontmatter title
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    body = text
    if fm:
        m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm.group(1), re.M)
        if m:
            title = m.group(1).strip()
        body = text[fm.end() :]
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.M)
        title = m.group(1).strip() if m else "(no title)"
    for m in re.finditer(r"^##\s+(.+)$", body, re.M):
        h = m.group(1).strip()
        h = re.sub(r"\s*Direct link to.*$", "", h)
        h2.append(h)
        if len(h2) >= 12:
            break
    return title, h2


def main() -> int:
    repo = find_repo()
    out_dir = skill_dir() / "references"
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not repo:
        stamp = out_dir / "LAST_REFRESH.md"
        stamp.write_text(
            f"# Last refresh\n\n"
            f"- **status:** failed — no hermes-agent checkout found\n"
            f"- **attempted_at:** {now}\n"
            f"- **searched:** HERMES_AGENT_REPO, $HERMES_HOME/hermes-agent, cwd\n\n"
            f"Install or set HERMES_AGENT_REPO, then re-run.\n",
            encoding="utf-8",
        )
        print("ERROR: hermes-agent checkout not found", file=sys.stderr)
        return 1

    doc_root = repo / "website/docs/developer-guide"
    if not doc_root.is_dir():
        doc_root = repo / "docs/developer-guide"

    info = git_info(repo)
    lines = [
        f"# Doc headings snapshot",
        f"",
        f"Generated: {now}",
        f"Source: `{info['remote']}`",
        f"Commit: `{info['commit']}` ({info['branch']}) — {info['subject']}",
        f"",
    ]
    doc_pages = sorted(path.relative_to(doc_root) for path in doc_root.rglob("*.md"))
    found = 0
    for rel in doc_pages:
        path = doc_root / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        title, h2 = extract_heading_meta(text)
        found += 1
        lines.append(f"## {rel}")
        lines.append(f"- title: {title}")
        lines.append(f"- bytes: {len(text.encode('utf-8'))}")
        if h2:
            lines.append("- h2:")
            for h in h2:
                lines.append(f"  - {h}")
        lines.append("")

    agents = repo / "AGENTS.md"
    agents_bytes = agents.stat().st_size if agents.is_file() else 0
    if agents.is_file():
        atext = agents.read_text(encoding="utf-8", errors="replace")
        _, ah2 = extract_heading_meta(atext)
        lines.append("## AGENTS.md")
        lines.append(f"- bytes: {agents_bytes}")
        lines.append("- h2:")
        for h in ah2[:20]:
            lines.append(f"  - {h}")
        lines.append("")

    (out_dir / "_doc_headings.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    stamp_lines = [
        "# Last refresh",
        "",
        f"- **status:** ok",
        f"- **refreshed_at:** {now}",
        f"- **source_remote:** {info['remote']}",
        f"- **git_commit:** `{info['commit']}`",
        f"- **git_branch:** `{info['branch']}`",
        f"- **git_subject:** {info['subject']}",
        f"- **git_date:** {info['date']}",
        f"- **developer_guide_pages_found:** {found}/{len(doc_pages)} (discovered recursively)",
        f"- **AGENTS.md_bytes:** {agents_bytes}",
        f"- **headings_snapshot:** `references/_doc_headings.md`",
        "",
        "## Agent follow-up",
        "",
        "1. Diff `_doc_headings.md` against prior version (if any).",
        "2. Re-read changed pages under `website/docs/developer-guide/`.",
        "3. Patch `SKILL.md` / `references/architecture-snapshot.md` / `extension-map.md` if ladders or file maps drifted.",
        "4. Optionally refresh related skill `hermes-agent` for user-facing CLI/config changes.",
        "",
        "## Live docs",
        "",
        "https://hermes-agent.nousresearch.com/docs/developer-guide/",
        "",
    ]
    (out_dir / "LAST_REFRESH.md").write_text("\n".join(stamp_lines), encoding="utf-8")

    print(f"Refreshed from {repo} @ {info['commit']}")
    print(f"  pages: {found}/{len(doc_pages)}")
    print(f"  wrote: {out_dir / 'LAST_REFRESH.md'}")
    print(f"  wrote: {out_dir / '_doc_headings.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
