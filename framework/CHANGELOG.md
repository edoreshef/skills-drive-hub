# Changelog

## 0.1.6

2026-10-22: what the first reviews of other people's submissions found. `.pytest_cache` is skipped like `__pycache__`
(a package release shipped one), and check's size warning counts the same files a release ships (it warned
"large size increase" on seven untouched skills because their tests had written `__pycache__`). Maintainer side, not
shipped: `unpack.py` gives back a release's source tree from Drive or a zip, optionally with an inbox submission laid
over its skill, so a review compares against what users have even when the repo lags; `gate.strip_gate` is the
inverse of the gate release adds. authoring.md has the review routine and the release-maintainer's housekeeping.

## 0.1.5

2026-10-12: Mac, before the first user (Mac installs are not measured yet). START HERE step 2 looks before it
changes anything, installs `uv` into the home folder by two named routes (the official installer, else an existing
Homebrew) and otherwise stops; no `sudo`, nothing that opens a system dialog. Where `python3` is not a usable Python, as
on a Mac without Apple's Command Line Tools (running it opens their install dialog), START HERE and the `sync`,
`feedback` and `publish` skills run each tool as `uv run --python-preference only-managed --script <tool>.py`: `uv`'s
own Python, no administrator. `feedback` and `publish` say `python3`, not `python`. Step 9 asks for feedback after
every Mac install, smooth or not. Install, doctor, sync and a gated package script were run this way on Linux (uv 0.10.0).

## 0.1.4

2026-10-11: what the first Claude Science run found (spike S12). `install.py --from-tool-result` accepts the zip's own
bytes (Science's kernel saves those; it failed with a UnicodeDecodeError). Every tool puts its own directory on
`sys.path` before importing `common`, so `PYTHONSAFEPATH=1` (Science's sandbox) no longer breaks `python3 <abs path>`.
The install root defaults to `SKILLS_HUB_ROOT` when set, and the sync gate reads that root and fails closed; on
Science `~` does not persist, so START HERE sets the variable to a workspace path (S10 answered). START HERE and the
`sync` skill carry the Science branch.

## 0.1.3

2026-10-11: `install.py` writes `<root>/.claude-plugin/marketplace.json` (the local directory marketplace Claude Code registers once; one plugin per installed tree), which the design promised but no tool wrote. START HERE step 7 now gives the exact `claude plugin` commands and allow rules. Found by the first agent-driven START HERE run (headless Claude Code, spike S11).

## 0.1.2

2026-10-11: the framework tree keeps the placeholder maintainer `r&d@example.com`; `release.py` substitutes the deployment's maintainer into the zip (`--maintainer`, else the registry's account). 0.1.1 had the address edited into the repo instead.

## 0.1.1

2026-10-11: the maintainer of this deployment is named. `check.py` skips `.git/` and runs a skill's tests from any working directory. Maintainer side: `setup_drive.py` and `release.py --upload` (Drive API).

## 0.1.0

Initial Skills Hub: install, sync, link, doctor, stale reminder, check, draft, publish. Extras: feedback.
