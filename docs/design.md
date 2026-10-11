# Design

## Goal

Skills Hub lets an organization share agent skills through Google Drive. Domain experts who do
not use git or a terminal **get** skill packages, keep them **current**, **contribute** back, and
give **feedback** on whether skills worked, from inside their AI host. Hosts: Claude Code, Claude Science, Cursor. OS: macOS, Windows, Linux.

Three layers, each versioned on its own:

- **Skills Hub, the framework** (this repo). The sharing tools: install, sync, publish, review, release. Every user installs it once.
- **Foundation package.** Cross-domain skills, maintained by the Skills Hub maintainers.
- **Domain packages.** One per domain, maintained by that domain's experts with the same tools.

A user installs Skills Hub, the foundation package, and the domain packages they work in.
A domain release never rebuilds Skills Hub, and a Skills Hub release never rebuilds content.

## Decisions

Evidence for the spike references (S1–S10) is in [`spikes/README.md`](../spikes/README.md).

| Decision | Why |
|---|---|
| Storage is SSO-gated Google Shared Drives. | Users already have Drive behind SSO. No S3, CloudFront, GitHub, or Drive for desktop to provision. |
| Transport is the host's Google Drive connector. Package files are fetched by file ID with `download_file_content`, never `read_file_content`. | `read_file_content` returns a Markdown rendering; `download_file_content` is byte-exact (S1). Listings paginate, so fetch by ID (S1). |
| Each package has one mutable file, `current.json`, with a fixed file ID. Releases are new immutable zips. `current.json` is rewritten last, by a Drive API media update. | The connector's `update_file` cannot change bytes (S2). Writing the pointer last means a half-uploaded release is never pointed at. |
| `install.py` checks sha256 and size before writing anything, then swaps `staging → current`. | A `current.json` is copied by the model, and a host can change how it returns results. The hash catches a bad copy (S1, S9). |
| Release zips are padded to at least 64 KiB with a stored `padding.bin`, which install drops. Agents never retype a zip. | Claude Code returns a result of up to 50,000 characters inline. A 26 KB zip came back inline, and the model's copy took 17 minutes and was wrong. A larger zip is saved to a file that the tools read directly (S9). |
| Two Shared Drives per package: Published (users read) and Submissions (authors write). Members are people or a Google Group; Drive refuses domain-wide sharing on a Shared Drive (tested 2026-10-11). | A Shared Drive role applies to every folder in it. A maintainer of one package must not be able to write another package or the framework. "All users" is one Group added as Viewer. |
| Only the framework zip carries the installer. A content zip containing `tools/install.py` is refused at release and at install. | A domain release must not be able to replace the installer. |
| Scripts never contain credentials and never write to a data source. A script may read data with the user's own token from `~/.config/<org>/`, outside every package and outside `~/.skills-hub/`; `check.py` warns on the literal path and on network imports, and the maintainer accepts those warnings for such a script. (Until 2026-10-11 the rule was that scripts never fetch data at all.) | The foundation package is also the reference code for reaching the organization's data, and a program such as a dashboard imports it. The token is per user and SSO-gated like the host's connectors. A skill still documents the connector route for hosts where Python has no network (Claude Science). |
| Released scripts carry a sync gate. A content script runs only if its package was checked within 24 hours and no newer version is pending. `release.py` adds the gate; the package repos never have it. | Skills must stop working when they may be out of date, and prose instructions do not enforce that. Injecting at release keeps authors' sources and tests ungated. |
| Scripts declare dependencies with PEP 723: a bare name or an exact `==` pin. Claude Code and Cursor run them with `uv run --script`; Claude Science installs with `manage_packages` and runs `python`. | Claude Science has no `uv`, and its package tool rejects ranges (S3). |
| Claude Code loads `~/.skills-hub` as a local directory marketplace. Cursor gets one symlink per package. Claude Science publishes each skill through `host.skills` after two standing grants. | What each host actually loads (S3, S4, S5). Details in [`hosts.md`](hosts.md). |
| Feedback is one file per entry, created with `create_file`. Maintainers collect files into their Sheet. | The connector cannot append Sheet rows (S1, S2). |
| Each content package has its own git repo, one tag per release. Drive is what users read; git is the record. This repo holds no content. | Domains own their content and release on their own schedule. |
| Checks only block on broken structure. Everything else is a warning in the review report. | Maintainers judge; the tool should not stop a sound submission. |
| No admin step. One agent-guided install per user, from the START HERE doc on the Skills Hub drive. | No MDM or org-wide plugin push is assumed. |

## Drive layout

```text
"Skills Hub — Published"                  managers: Skills Hub maintainers; users: Viewer
├── START HERE (Google Doc)               source: docs/start-here.md
├── current.json                          fixed file ID
├── releases/skills-hub-<version>.zip
└── index.json                            per package: slug, title, maintainers, current.json file ID

"<package> — Published"                   managers: that package's maintainers; users: Viewer
├── START HERE (Google Doc)
├── current.json                          fixed file ID
└── releases/<package>-<version>.zip

"<package> — Submissions"                 maintainers: Manager; authors: Contributor
├── inbox/<skill>__<yyyymmdd-hhmm>__<author>.zip
├── accepted/   rejected/                 moved here with a REVIEW.md
├── feedback/<yyyymmdd-hhmm>__<author>__<skill>.json    one file per feedback entry
└── Feedback (Sheet)                                     collected by maintainers
```

The Skills Hub maintainers update `index.json` when a package is registered. Domains do not write it.

## Release format

A release zip holds the package tree plus `manifest.json` (path, sha256, and size of every file).
A zip under 64 KiB also gets `padding.bin`, bytes derived from the zip's hash, so equal input still
gives an equal zip. The manifest does not list it. In a content zip, every `skills/<skill>/scripts/**/*.py`
carries the sync gate from `maintainer/gate.py`; the manifest lists the gated bytes, and release refuses a
script that the gate pushes over 64 KiB.
`maintainer/release.py --dry-run` builds the zip, `manifest.json`, and `current.json`:

```json
{
  "package": "irrigation",
  "version": "0.4.0",
  "min_version": "0.3.0",
  "zip_file_id": "1AbC…",
  "zip_sha256": "…",
  "zip_bytes": 184320
}
```

A content package:

```text
.claude-plugin/plugin.json     name: <slug>
package.json                   package, title, maintainers, version
CHANGELOG.md
skills/<skill>/                see authoring.md
```

The framework zip, `skills-hub-<version>.zip`, is the `framework/` directory of this repo: the
`skills-hub` plugin manifest, the `sync`, `publish`, and `feedback` skills, the SessionStart hook,
`tools/`, and `templates/`. A content package may not use the `skills-hub` slug.

Release refuses anything `check.py` blocks, plus a framework zip with non-framework skills.

## On the user's machine

```text
~/.skills-hub/
├── framework/current/                 the framework zip, unpacked
├── packages/<slug>/current/           one tree per package; previous/ kept after a swap
├── marketplace.json                   Claude Code: one entry per installed plugin
├── state.json                         per package: version, sha256, bytes, current_file_id, last_check, pending_version
├── links.json                         Cursor: links that link.py created
└── drafts/<slug>/<skill>/             author drafts
```

## Install and sync

First install follows [`start-here.md`](start-here.md). Sync, per package:

1. **Remind.** Claude Code's SessionStart hook runs `stale.py`, which prints one line if any package was last checked over 24 hours ago or has an update pending. Local only.
2. **Check.** Download that package's `current.json` by the file ID in `state.json`. Same version: refresh `last_check`, clear `pending_version`, and stop. Another version: record it as `pending_version`.
3. **Fetch.** Download the zip by `zip_file_id`. The host saves it to a tool-result file, which `install.py --from-tool-result` and `sync.py` read directly. If a zip comes back inline, the agent stops instead of retyping it. The fix is `MAX_MCP_OUTPUT_TOKENS` set to 2000 in the user's Claude Code settings `env`.
4. **Verify and swap.** sha256 and size must match. On mismatch nothing changes; retry once, then stop. Other packages are never touched.
5. **Load.** Cursor: `link.py`. Claude Science: `host.skills` for changed skills. Then `doctor.py`.

A successful install rewrites the package's record with a fresh `last_check` and no `pending_version`.

### The sync gate

A gated script checks its own package before it does anything else:

- Under `<root>/packages/<slug>/current/` (Claude Code, and Cursor through its symlink) it reads that root's `state.json` and fails closed. A missing or damaged file or record blocks it.
- Anywhere else, it reads `~/.skills-hub/state.json` if that exists and fails closed the same way. This covers a copy run from Claude Code's plugin cache.
- With `SKILLS_HUB_ROOT` set (Claude Science: a workspace path, since `~` does not persist there) it reads that root's `state.json` and fails closed.
- With neither, it prints a warning and runs.

It blocks, with exit code 75 and one stderr line telling the agent to run sync, when `last_check` is over 24 hours old, in the future, or unreadable, or when `pending_version` is set.

Every newer version now blocks scripted skills until it is installed, so `min_version` no longer
changes what users can run. `sync.py` still reports it, and `current.json` keeps the field. It is the oldest
version *of that package* a user may keep using, not a framework version (an agent read it the other way, S12).

Skills with no script are not gated. The gate is a guardrail against using stale skills by
accident, not a security control: an agent can edit `state.json` or work around the script.

`doctor.py` reports a skill name that two installed packages both define. The package installed
later is blocked for that skill; `link.py` leaves the skill out of its Cursor link.

## Contribution

1. **Draft** from the template in `~/.skills-hub/drafts/<slug>/<skill>/`. On Claude Science the draft is a catalog draft (`host.skills.edit` without publish).
2. **Publish.** The `publish` skill runs the structure check, asks why, appends to `CHANGES.md`, writes `submission.json`, zips the skill, and uploads it to that package's `inbox/` with `create_file`. It downloads the file back and compares sha256.
3. **Review.** A maintainer of that package runs `maintainer/review.py`. If the submitter is not the skill owner, the maintainers tell the owner.
4. **Decide.** Accept: commit to the package's repo and move the zip to `accepted/` with REVIEW.md. Reject: `rejected/` with REVIEW.md. The author's agent can read the outcome through the connector.
5. **Release.** Bump the version and CHANGELOG, build, upload the zip, check Drive's `sha256Checksum`, rewrite `current.json` last, tag the repo.

The next sync on each user's machine brings the release to everyone who has that package.

## Feedback

The `feedback` skill asks which package and skill, asks consent, and writes one JSON file to
that package's Submissions drive under `feedback/`. `maintainer/collect-feedback.py` turns new
files into CSV rows for the package's Feedback Sheet.

A first install or a sync that was not smooth is a call for feedback, even when it ended well.
START HERE's last step and the `feedback` skill tell the agent to offer it whenever a step needed
a retry, a workaround, or a departure from the written steps. Such an entry is recorded against
`skills-hub` with skill `install` or `sync`, carries the Skills Hub version from `doctor.py`
(Skills Hub is not in `state.json`), and goes to the foundation package's `feedback/` folder,
since the Skills Hub maintainers maintain that package. Consent is still required.

## Security

- Write access to a package's Published drive is that package's trust boundary. The hash detects corruption, not a compromised maintainer: `current.json` and the zip live on the same drive.
- Domain maintainers are trusted for their package only.
- Submissions are untrusted. Any Contributor can edit the inbox, so review the snapshot you pulled and check Drive's revision history.
- Skill prose is instructions to the agent. Review the prose, not only the scripts.
- No credentials in any package; release and install refuse credential-like files.
- The sync gate keeps stale scripts from running by accident. It does not stop an agent that edits `state.json` or the script.
- Keep a second Manager on each Published drive.

## Status

Built and tested locally: every tool in `framework/tools/`, the three framework skills, the
maintainer tools, dry-run releases, and the sync gate in released scripts, exercised against the two fixture packages. START HERE
and sync also ran end to end through the claude.ai connector on the Claude Code CLI (S9).

Built 2026-10-11 and run against a real Google Workspace (Oddity Labs, Shared Drives): `maintainer/setup_drive.py`
(the drives, folders, START HERE docs, `index.json`), `release.py --upload` (immutable zip, `sha256Checksum` check,
`current.json` media update in place; a second release of the same version refused), and the user side replayed from
the real artifacts: START HERE steps 3–8, then a release bump → `sync.py` marks `pending_version` → a gated script
exits 75 → zip sync → the script runs. Drive returned `sha256Checksum` for every upload to a Shared Drive.

Not built:

- Installing or syncing Skills Hub itself. START HERE installs it with a manual decode and hash check; `install.py` and `sync.py` handle content packages only.

Not tested:

- The largest result `download_file_content` can return. 313,125 characters worked (S9).
- `uv` install without admin on macOS and Windows, behind a proxy, or with Defender.
- That a maintainer of one package cannot write another's Published drive (`sha256Checksum` on a Shared Drive: tested, works).
- Marketplace registration from the desktop app (two plugins in one local marketplace: tested, S11).
- Whether Cursor's `sessionStart` hook output reaches the agent. Until it does, Cursor users run sync by hand.
- Whether the Claude Science sandbox can write its own grants. Until it can, START HERE sets them from the host (the maintainer's browser session can, S12).
- The sync gate in Cursor sessions (Claude Code: tested, S11).
- Windows junctions in `link.py`.

Decided 2026-10-11: the foundation package is `<org>-foundation` (its own repo). It owns the
`~/.config/<org>/` secrets layout and a single constants module (`data-sources/scripts/settings.py`)
holding every Drive, Sheet, folder and data-source ID; functions take IDs as parameters and never
hardcode them. Domain IDs split out to domain packages only if foundation releases start being driven
by ID changes. A program that imports a released foundation script meets the import-time sync gate and
must turn exit code 75 into "run the sync skill" for its user.

Open decisions:

- A per-zip size budget, if one fetch cannot carry a whole package.
- A backup reviewer for each package.
- How a skill owner hears about a non-owner edit (v1: the maintainers message them).
- Which remote Google Drive MCP Cursor users add. Cursor has no claude.ai connectors, so this blocks Cursor distribution.
