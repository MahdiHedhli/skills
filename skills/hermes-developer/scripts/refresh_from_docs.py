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


DOC_PAGES = [
    "contributing.md",
    "architecture.md",
    "agent-loop.md",
    "prompt-assembly.md",
    "context-compression-and-caching.md",
    "session-storage.md",
    "provider-runtime.md",
    "programmatic-integration.md",
    "adding-tools.md",
    "adding-providers.md",
    "adding-platform-adapters.md",
    "plugins/index.md",
    "plugin-llm-access.md",
    "memory-provider-plugin.md",
    "context-engine-plugin.md",
    "secret-source-plugin.md",
    "model-provider-plugin.md",
    "image-gen-provider-plugin.md",
    "video-gen-provider-plugin.md",
    "web-search-provider-plugin.md",
    "browser-provider-plugin.md",
    "creating-skills.md",
    "extending-the-cli.md",
    "tools-runtime.md",
    "browser-supervisor.md",
    "gateway-internals.md",
    "acp-internals.md",
    "cron-internals.md",
    "trajectory-format.md",
]


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
    info = {"commit": "unknown", "branch": "unknown", "subject": "", "date": ""}
    try:
        def run(*args: str) -> str:
            return subprocess.check_output(
                ["git", "-C", str(repo), *args],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()

        info["commit"] = run("rev-parse", "--short", "HEAD")
        info["branch"] = run("rev-parse", "--abbrev-ref", "HEAD")
        info["subject"] = run("log", "-1", "--pretty=%s")
        info["date"] = run("log", "-1", "--pretty=%cI")
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
        f"Repo: `{repo}`",
        f"Commit: `{info['commit']}` ({info['branch']}) — {info['subject']}",
        f"",
    ]
    missing: list[str] = []
    found = 0
    for rel in DOC_PAGES:
        path = doc_root / rel
        if not path.is_file():
            missing.append(rel)
            lines.append(f"## MISSING: {rel}")
            lines.append("")
            continue
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

    (out_dir / "_doc_headings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    stamp_lines = [
        "# Last refresh",
        "",
        f"- **status:** ok",
        f"- **refreshed_at:** {now}",
        f"- **repo:** `{repo}`",
        f"- **git_commit:** `{info['commit']}`",
        f"- **git_branch:** `{info['branch']}`",
        f"- **git_subject:** {info['subject']}",
        f"- **git_date:** {info['date']}",
        f"- **developer_guide_pages_found:** {found}/{len(DOC_PAGES)}",
        f"- **missing_pages:** {', '.join(missing) if missing else '(none)'}",
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
    print(f"  pages: {found}/{len(DOC_PAGES)}  missing: {len(missing)}")
    print(f"  wrote: {out_dir / 'LAST_REFRESH.md'}")
    print(f"  wrote: {out_dir / '_doc_headings.md'}")
    return 0 if not missing else 0  # missing pages noted but non-fatal


if __name__ == "__main__":
    raise SystemExit(main())
