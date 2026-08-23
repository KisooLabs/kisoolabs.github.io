# Publishing a KisooLabs program

How a program gets from a local build to a download on kisoolabs.github.io. Written after publishing Windows Hello Auto-Click (2026-08-23), which is the worked example throughout.

## 1. Decide what is public

Two separate questions. Answering them as one is the mistake that wastes the most time.

**Does the source go public?** Usually no. Most programs here are closed-source freeware.

**Where does the download live?** It has to be a **public** repo, whatever the source decision was. GitHub release assets on a private repo require authentication, so an anonymous visitor gets a 404. Verified:

```
private repo release page  -> HTTP 404
public  repo release page  -> HTTP 302
public  repo asset         -> HTTP 200
```

A public repo does **not** have to contain source. `KisooLabs/windows-hello-auto-click` is public and holds exactly `README.md` and `LICENSE`; the installer is a release asset and the application source is nowhere in it.

| | Source repo | Download repo | Site page |
|---|---|---|---|
| Closed source (default) | private, or local only | public, docs + releases only | `kisoolabs.github.io/<slug>/` |
| Open source | public, the same repo serves both | | `kisoolabs.github.io/<slug>/` |

## 2. Give each program its own release host

**Do not publish a second program's releases on `kisoolabs.github.io`.** That repo already hosts MacTab's, and `releases/latest` is **one pointer per repo, not per product**. A new non-prerelease release anywhere in that repo becomes `latest`, and every `releases/latest/download/MacTab*` link 404s the moment it does.

So each program gets its own public repo, and its download URL stays stable across versions:

```
https://github.com/KisooLabs/<repo>/releases/latest/download/<Asset>.exe
```

Two rules that keep it stable:

- **The asset filename carries no version.** Upload `WindowsHelloAutoClick-Setup.exe`, not `...-0.4.3.exe`. The version belongs in the tag and the release title. A versioned asset name breaks `latest/download/` on every release.
- **Do not mark the release as a prerelease** unless you mean it. `latest` skips prereleases.

MacTab predates this rule and still publishes into the site repo. Leave it there. If a second product ever needs to publish into the site repo, pin every download link to its tag (`releases/download/<tag>/<Asset>`) first.

## 3. Build and verify before anything is public

1. Build the installer. Confirm the version in the project file and the installer script agree (`build-installer.ps1` fails the build when they do not).
2. **Install it through the real wizard once**, not only silently. Silent installs skip `skipifsilent` steps, so the final "Launch now" step is never exercised. That exact step shipped broken in Windows Hello Auto-Click 0.4.1 (`CreateProcess failed; code 740`) and a silent test would not have caught it.
3. Scan it the way a downloader receives it: copy to `~\Downloads`, attach a Mark of the Web `Zone.Identifier`, then `MpCmdRun.exe -Scan -ScanType 3 -File <path>`. Scanning it in place under `Sharing\` returns "skipped", because synced folders are commonly excluded from Defender.
4. Record the SHA-256.

## 4. Publish the release

```bash
gh repo create KisooLabs/<repo> --public --source=. --remote=origin --push \
  --description "<one line>"

gh release create v<version> <Asset>.exe SHA256.txt \
  --repo KisooLabs/<repo> \
  --title "<Product> <version>" \
  --notes-file notes.md
```

`SHA256.txt` holds one line, `<hash>  <asset filename>`, matching `Get-FileHash` output so a user can compare directly.

Then confirm the public path actually resolves, unauthenticated:

```bash
curl -sIL -o /dev/null -w "%{http_code}\n" \
  https://github.com/KisooLabs/<repo>/releases/latest/download/<Asset>.exe
curl -sL https://github.com/KisooLabs/<repo>/releases/latest/download/SHA256.txt
```

## 5. Add the site page

Each product is a folder in this repo: `<slug>/index.html`, `<slug>/styles.css`, `<slug>/assets/`.

The fastest honest start is to copy `mactab/styles.css`, which is token-driven. Recolour by editing `--accent`, `--accent-2`, `--accent-3` and the two hardcoded hover values (`rgba(15,118,214,.28)`, `background:#0c67bd`). Replace MacTab's hero mock rules (`.mock`, `.mrow`, `.mprev`, `.win-*`) with something that shows your product; keep `.hero-art`. Fonts are shared at `../fonts/Geist-*.woff2`.

Reuse the page skeleton from `mactab/index.html`: sticky nav, hero (icon, eyebrow, `h1` with a `.grad` span, `.hero-sub`, `.hero-cta`, `.hero-note`, `.hero-art`), feature sections, a `#get` section, footer.

Then add a card at the top of the programs list in the root `index.html`:

```html
<article class="prog reveal">
  <div class="prog-thumb"><img src="<slug>/assets/thumb.svg" alt="..."></div>
  <div class="prog-body">
    <div class="prog-title"><h3>Name</h3><span class="plat"><!-- platform svg --></span></div>
    <p class="prog-desc">One or two sentences.</p>
    <div class="prog-actions"><a class="pbtn" href="<slug>/">See program <span class="arr">→</span></a></div>
  </div>
</article>
```

Thumbnails are 640×360 SVG. Icons are 256×256 SVG with a rounded rect and a white glyph.

**Check it in a browser before pushing.** Serve the repo (`python -m http.server 8731`), open the product page and the index, and look at both.

## 6. Say the uncomfortable things on the page

A download page that lists only benefits is a page that misleads. Whatever is true of the build, state it where a visitor will read it:

- **Unsigned.** Say SmartScreen will warn, say the warning is doing its job, and publish the SHA-256 as the substitute for a signature. Do not tell people to ignore security warnings without giving them something to check instead.
- **Requires Administrator.** Say why, structurally. "It writes under HKEY_LOCAL_MACHINE" is an answer; "it needs it" is not.
- **Anything it removes.** Windows Hello Auto-Click automates a consent step, so the page has a section on exactly that, including who should not install it. If a program changes a security or privacy boundary, that belongs in its own section, not a footnote.

The same text belongs in the download repo's `README.md`, the release notes, and the site page. Three places, one message.

## 7. If the site does not update

This repo deploys through a GitHub Actions workflow, not the legacy Pages pipeline, so `gh api .../pages/builds/latest` reports a stale date and tells you nothing. Check `gh run list --repo kisoolabs/kisoolabs.github.io` instead.

Pages deployments to the `github-pages` environment are serialized, and a run stuck in `waiting` or `queued` blocks every later one indefinitely. On 2026-08-23 a push deployment sat `pending` behind two abandoned runs, one `waiting` since 2026-08-06 and one `queued` since 2026-07-05. Cancelling both drained the queue and the new run went green within seconds:

```bash
gh run list --repo kisoolabs/kisoolabs.github.io --limit 40 \
  --json databaseId,status,displayTitle \
  --jq '.[] | select(.status != "completed") | "\(.databaseId)  \(.status)  \(.displayTitle)"'
gh run cancel <id> --repo kisoolabs/kisoolabs.github.io
```

Cancelling a stale run does not touch the live site, which is already serving the last successful deployment.

## 8. Afterwards

- Re-check any *other* product's download links if you touched a shared repo.
- Update the product's own `STATUS.md` / `TODO.md` in its source folder.
- Commit the site repo and push. GitHub Pages redeploys on push.

## Worked example: Windows Hello Auto-Click

| Piece | Where |
|---|---|
| Source (private) | `Development/Windows Hello Auto/` |
| Download repo (public, docs only) | `KisooLabs/windows-hello-auto-click` + `Development/windows-hello-auto-click/` |
| Installer | release asset `WindowsHelloAutoClick-Setup.exe` on tag `v0.4.3` |
| Stable download URL | `https://github.com/KisooLabs/windows-hello-auto-click/releases/latest/download/WindowsHelloAutoClick-Setup.exe` |
| Site page | `windows-hello-auto-click/` in this repo |
