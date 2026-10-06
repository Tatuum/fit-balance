#!/usr/bin/env python3
"""Maintain CHANGELOG.md from git commit history."""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def git_log():
    """Return commits as {date: [subject, ...]}, newest-first overall and
    newest-first within each date, ordered newest-first."""
    cmd = ["git", "log", "--format=%ad|%s", "--date=short"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    by_date = defaultdict(list)
    for line in result.stdout.strip().splitlines():
        if "|" in line:
            date, subject = line.split("|", 1)
            by_date[date.strip()].append(subject.strip())
    return by_date


def parse_existing(text):
    """Parse an existing CHANGELOG.md into {date: [subject, ...]}, same
    shape/order as git_log(), by reading its own `## YYYY-MM-DD` / `- ...`
    structure back out -- so merging never depends on date granularity."""
    by_date = defaultdict(list)
    current = None
    for line in text.splitlines():
        heading = re.match(r"^## (\d{4}-\d{2}-\d{2})\s*$", line)
        if heading:
            current = heading.group(1)
            continue
        bullet = re.match(r"^- (.+)$", line)
        if bullet and current:
            by_date[current].append(bullet.group(1).strip())
    return by_date


def render_sections(by_date):
    lines = []
    for date in sorted(by_date, reverse=True):
        lines.append(f"\n## {date}\n")
        for subject in by_date[date]:
            lines.append(f"- {subject}\n")
    return lines


def main():
    changelog = Path("CHANGELOG.md")

    if not changelog.exists():
        by_date = git_log()
        if not by_date:
            print("No commits found — nothing to write.")
            sys.exit(0)
        content = ["# Changelog\n"] + render_sections(by_date)
        changelog.write_text("".join(content))
        total = sum(len(v) for v in by_date.values())
        print(f"Created CHANGELOG.md with {total} entries across {len(by_date)} date(s).")
        return

    existing_by_date = parse_existing(changelog.read_text())
    all_commits = git_log()

    # For each date, the changelog's existing entries should be a suffix of
    # git log's current (newest-first) list for that date -- new commits
    # land at the front over time. Whatever's left over at the front is
    # new. This catches commits made *after* a prior run on the same date,
    # which comparing whole dates (the previous approach) missed entirely.
    new_by_date = defaultdict(list)
    found_new = False
    for date, current in all_commits.items():
        recorded = existing_by_date.get(date, [])
        new_count = len(current) - len(recorded)
        if new_count > 0:
            new_by_date[date] = current[:new_count]
            found_new = True

    if not found_new:
        print("No new commits since last entry — CHANGELOG.md is up to date.")
        sys.exit(0)

    merged = defaultdict(list)
    for date, subjects in new_by_date.items():
        merged[date] = subjects + existing_by_date.get(date, [])
    for date, subjects in existing_by_date.items():
        if date not in merged:
            merged[date] = subjects

    changelog.write_text("# Changelog\n" + "".join(render_sections(merged)))
    total = sum(len(v) for v in new_by_date.values())
    print(f"Added {total} new entries to CHANGELOG.md.")


if __name__ == "__main__":
    main()
