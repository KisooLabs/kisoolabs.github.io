#!/usr/bin/env python3
"""Regenerate every notes/programs listing from data/site.json.

Run after publishing a note or adding a program:

    python tools/build_site.py

Rewrites the marked regions of index.html and notes/index.html, and
regenerates notes/feed.xml in full. Nothing else in those files is touched.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://kisoolabs.github.io"

PLATFORM_ICONS = {
    "windows": (
        '<svg viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="Windows">'
        "<title>Windows</title>"
        '<path d="M3 3h8.5v8.5H3zM12.5 3H21v8.5h-8.5zM3 12.5h8.5V21H3zM12.5 12.5H21V21h-8.5z"/></svg>'
    ),
    "macos": (
        '<svg viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="macOS">'
        "<title>macOS</title>"
        '<path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 '
        "3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.03 1.52-.065 2.09-.987 "
        "3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 "
        "1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 "
        "2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 "
        '3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 '
        '2.338-1.273 3.714 1.338.104 2.715-.688 3.56-1.702"/></svg>'
    ),
    "web": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        'role="img" aria-label="Web"><title>Web</title><circle cx="12" cy="12" r="9"/>'
        '<path d="M3 12h18M12 3c2.8 3.4 2.8 14.6 0 18M12 3c-2.8 3.4-2.8 14.6 0 18"/></svg>'
    ),
    "chrome": (
        '<svg viewBox="0 0 24 24" fill="currentColor" role="img" aria-label="Chrome extension">'
        "<title>Chrome extension</title>"
        '<path d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 '
        "0-2 .9-2 2v3.8h1.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0"
        "-1.49 1.21-2.7 2.7-2.7 1.49 0 2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 "
        '2.5-2.5S21.88 11 20.5 11z"/></svg>'
    ),
    "vscode": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="VS Code">'
        "<title>VS Code extension</title>"
        '<path d="M8.4 8.6 4.6 12l3.8 3.4M15.6 8.6 19.4 12l-3.8 3.4M13.4 6.2l-2.8 11.6"/></svg>'
    ),
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def pretty_date(dt: datetime) -> str:
    return f"{MONTHS[dt.month - 1]} {dt.day}, {dt.year}"


def short_date(dt: datetime) -> str:
    return f"{MONTHS[dt.month - 1]} {dt.day}, {dt.year}"


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def write(path: Path, text: str) -> None:
    """Write with LF endings so the generated diff stays platform-neutral."""
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_block(text: str, name: str, body: str, path: Path) -> str:
    start = f"<!-- BUILD:{name}:start -->"
    end = f"<!-- BUILD:{name}:end -->"
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end), re.DOTALL
    )
    if not pattern.search(text):
        sys.exit(f"error: markers BUILD:{name} not found in {path}")
    return pattern.sub(f"{start}\n{body}\n        {end}", text, count=1)


def build_home_notes(notes: list[dict], limit: int) -> str:
    rows = []
    for note in notes[:limit]:
        dt = parse_date(note["date"])
        blurb = note.get("short") or note["summary"]
        rows.append(
            f'          <a class="note-row reveal" href="notes/{note["slug"]}/">\n'
            f'            <p class="nr-kicker">{note["kicker"]}</p>\n'
            f'            <div class="nr-head">\n'
            f'              <h3>{note["title"]} <span class="arr">→</span></h3>\n'
            f'              <time datetime="{note["date"]}">{pretty_date(dt)}</time>\n'
            f"            </div>\n"
            f'            <p class="nr-sub">{blurb}</p>\n'
            f"          </a>"
        )
    return "\n".join(rows)


def build_programs(programs: list[dict], notes: list[dict]) -> str:
    by_program: dict[str, list[dict]] = {}
    for note in notes:
        if note.get("program"):
            by_program.setdefault(note["program"], []).append(note)

    blocks = []
    for prog in programs:
        icons = "".join(
            f"\n                {PLATFORM_ICONS[p]}" for p in prog["platforms"]
        )
        target = (
            ' target="_blank" rel="noopener"' if prog.get("external") else ""
        )
        arrow = "↗" if prog.get("external") else "→"

        actions = [
            f'              <a class="pbtn" href="{prog["href"]}"{target}>'
            f'See program <span class="arr">{arrow}</span></a>'
        ]
        store = prog.get("store")
        if store:
            actions.append(
                f'              <a class="pbtn" href="{store["href"]}"'
                f' target="_blank" rel="noopener">'
                f'{store["label"]} <span class="arr">↗</span></a>'
            )
        for note in by_program.get(prog["id"], []):
            dt = parse_date(note["date"])
            label = "Making note"
            actions.append(
                f'              <a class="pbtn note" href="notes/{note["slug"]}/">'
                f"{label} <time>· {short_date(dt)}</time></a>"
            )

        blocks.append(
            f'        <article class="prog reveal">\n'
            f'          <div class="prog-thumb"><img src="{prog["thumb"]}" alt="{prog["alt"]}"></div>\n'
            f'          <div class="prog-body">\n'
            f'            <div class="prog-title"><h3>{prog["name"]}</h3>\n'
            f'              <span class="plat">{icons}\n              </span>\n'
            f"            </div>\n"
            f'            <p class="prog-desc">{prog["desc"]}</p>\n'
            f'            <div class="prog-actions">\n'
            + "\n".join(actions)
            + f"\n            </div>\n"
            f"          </div>\n"
            f"        </article>"
        )
    return "\n\n".join(blocks)


def build_note_list(notes: list[dict]) -> str:
    items = []
    for note in notes:
        dt = parse_date(note["date"])
        items.append(
            f'      <a class="note-item reveal" href="{note["slug"]}/">\n'
            f'        <p class="note-kicker"><span>{note["kicker"]}</span>'
            f'<time datetime="{note["date"]}">{pretty_date(dt)}</time></p>\n'
            f'        <h2>{note["title"]} <span class="arr">→</span></h2>\n'
            f'        <p>{note["summary"]}</p>\n'
            f"      </a>"
        )
    return "\n".join(items)


def build_feed(notes: list[dict]) -> str:
    items = []
    for note in notes:
        dt = parse_date(note["date"])
        url = f"{SITE_URL}/notes/{note['slug']}/"
        pub = dt.strftime("%a, %d %b %Y 00:00:00 GMT")
        items.append(
            f"    <item>\n"
            f"      <title>{note['title']}</title>\n"
            f"      <link>{url}</link>\n"
            f'      <guid isPermaLink="true">{url}</guid>\n'
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <description>{strip_tags(note['summary'])}</description>\n"
            f"    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>Kisoo Kim — Notes</title>\n"
        f"    <link>{SITE_URL}/notes/</link>\n"
        "    <description>The stories behind the things I build — why each exists, "
        "and what building it taught me.</description>\n"
        "    <language>en</language>\n"
        f'    <atom:link href="{SITE_URL}/notes/feed.xml" rel="self" '
        'type="application/rss+xml"/>\n'
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def main() -> None:
    data = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    notes = sorted(data["notes"], key=lambda n: n["date"], reverse=True)
    programs = data["programs"]

    for note in notes:
        if not (ROOT / "notes" / note["slug"] / "index.html").exists():
            sys.exit(f"error: notes/{note['slug']}/index.html does not exist")
    known = {p["id"] for p in programs}
    for note in notes:
        if note.get("program") and note["program"] not in known:
            sys.exit(f"error: note '{note['slug']}' points at unknown program "
                     f"'{note['program']}'")

    home_path = ROOT / "index.html"
    home = home_path.read_text(encoding="utf-8")
    home = replace_block(home, "notes",
                         build_home_notes(notes, data["notes_on_home"]), home_path)
    home = replace_block(home, "programs", build_programs(programs, notes), home_path)
    write(home_path, home)

    index_path = ROOT / "notes" / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index = replace_block(index, "notelist", build_note_list(notes), index_path)
    write(index_path, index)

    write(ROOT / "notes" / "feed.xml", build_feed(notes))

    print(f"built: {len(notes)} notes, {len(programs)} programs")
    print("  index.html          (Recent Notes + Programs)")
    print("  notes/index.html    (full note list)")
    print("  notes/feed.xml      (RSS)")


if __name__ == "__main__":
    main()
