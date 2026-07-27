# Projects

Source for my software portfolio — <https://kisoolabs.github.io/>

A static site served by GitHub Pages from the repo root. No framework, no
bundler — the one build step regenerates the notes/programs listings.

## Layout

- `index.html` — home: Head, Recent Notes, Programs
- `notes/` — the Notes section (`index.html`, `feed.xml`, one folder per note)
- `mactab/`, `usagepop/`, `pdf-page-remover/` — project pages, each self-contained
- `styles.css`, `fonts/`, `assets/` — shared shell styling and assets
- `data/site.json` — **single source of truth** for the note list and program list
- `tools/build_site.py` — regenerates every listing from `data/site.json`

## Publishing a note

1. Write the note at `notes/<slug>/index.html`.
2. Add an entry to the `notes` array in `data/site.json` (`program: null` if the
   note isn't about one of the programs).
3. Run the build:

   ```
   python tools/build_site.py
   ```

That rewrites, from the one manifest:

- home `Recent Notes` (newest 5, controlled by `notes_on_home`)
- home `Programs` — each program's `Making note` button
- `notes/index.html` — the full list
- `notes/feed.xml` — RSS

Only the regions between `<!-- BUILD:*:start -->` / `<!-- BUILD:*:end -->`
markers are touched; everything else in those files is hand-written. The script
is idempotent and fails loudly if a note points at a missing folder or an
unknown program.

**Never hand-edit the generated regions or `feed.xml`** — the next build
overwrites them. Editing the listings by hand is what let the home page fall a
note behind in July 2026.

## Adding a program

Add an entry to the `programs` array in `data/site.json` (order in the array is
the display order — newest first) and run the build. Platform icons come from
`platforms`: `windows`, `macos`, `web`, `chrome`.
