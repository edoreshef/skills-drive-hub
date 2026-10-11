# skills-drive-hub

**Skills Hub** is a framework for sharing agent skills across an organization, with Google Drive
as the hub. Domain experts get skill packages, improve them, and share their changes back from
inside Claude Code, Claude Science, or Cursor. They need no git and no terminal: their agent
does the work through the host's Google Drive connector.

This repo is the framework. It holds no skill content; each package has its own repo.

## How sharing works

- **Packages.** Skills are shared in packages. A foundation package holds cross-domain skills,
  and each domain publishes its own package, maintained by that domain's experts. Every package
  lives on two SSO-gated Shared Drives: one users read from, one they submit to.
- **Get.** The user's agent follows a START HERE doc on Drive. It installs Skills Hub, then the
  packages the user works in, and checks every download against its sha256.
- **Stay current.** The `sync` skill picks up each package's newest release. A package's scripts
  refuse to run when it has not been checked for 24 hours or an update is waiting.
- **Contribute.** The `publish` skill checks a new or changed skill and submits it to that
  package's inbox.
- **Feedback.** The `feedback` skill records, with the user's consent, whether a skill worked,
  as one file in that package's `feedback/` folder. An install or sync that was not smooth is
  also a call for feedback; the agent offers it unprompted. `maintainer/collect-feedback.py`
  turns new files into rows for the package's Sheet.
- **Review and release.** That package's maintainers review the submission, commit it to the
  package's repo, and release a new version to Drive. The next sync brings it to everyone.

## Names

| What | Name |
|---|---|
| This repo | `skills-drive-hub` |
| What users install | Skills Hub, the `skills-hub` plugin |
| Install root on a user's machine | `~/.skills-hub/` |

"Framework" means the Skills Hub tools themselves, as opposed to content packages. They live in
`framework/` here and in `~/.skills-hub/framework/current/` once installed.

## Layout

```text
framework/          exactly what ships in the skills-hub zip
  skills/           sync, publish, feedback
  hooks/            SessionStart: stale reminder (Claude Code)
  tools/            install, sync, link, doctor, stale, check, draft, publish, feedback
  templates/        new package and new skill
maintainer/         release, review, collect-feedback (run by package maintainers, not shipped);
                    gate, the sync gate release adds to every content script
fixtures/packages/  two sample packages with different maintainers, used by the tests
tests/              end-to-end tests that run each tool as a subprocess
spikes/             pre-build experiments: results and the assets to rerun them
docs/
  design.md         architecture, decisions and why, status, open items
  hosts.md          how Claude Code, Cursor, and Claude Science load packages
  authoring.md      skill format, checks, review, release
  start-here.md     source of the START HERE doc users' agents follow
  explainer/        narrated explainer video (Remotion); not shipped
```

The tools are Python 3.9+ standard library only.

## Develop

```text
python -m unittest discover -s tests
python maintainer/release.py --dry-run --out dist                                       # skills-hub zip
python maintainer/release.py --dry-run --package fixtures/packages/domain-sample --out dist
```

A change to install, sync, linking, or how scripts run also needs a manual run on each host
whose behavior changed: install the dry-run zips, run a skill script, and sync two packages
so that one updates and the other stays. Record host results in `spikes/README.md`.

When testing through Drive, judge bytes only by sha256, never by what `read_file_content` shows.

## License

MIT. See [LICENSE](LICENSE).
