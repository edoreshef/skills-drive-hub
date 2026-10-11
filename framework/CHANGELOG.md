# Changelog

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
