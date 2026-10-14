# Authoring and review

## Skill folder

```text
<skill-name>/
  SKILL.md         frontmatter: name, description, owner, data_sources
  examples/        at least one file with a question, steps, and an answer
  CHANGES.md       a dated entry for every submission
  reference/       schemas and flows, read on demand        (optional)
  scripts/         *.py with a PEP 723 header               (optional)
  tests/           *.py that exit 0 when the script works   (optional)
  submission.json  written by publish
```

Keep `SKILL.md` short. If the skill has a script, give both commands, as the skill template does:

- Claude Code and Cursor: one absolute command, `uv run --script ~/.skills-hub/packages/<slug>/current/skills/<skill>/scripts/<name>.py`. Say to run it exactly as written, with no `cd` and no `python`. The allow rules match only this command.
- Claude Science: install each dependency with `manage_packages`, then `python scripts/<name>.py` from the published skill directory. Mark it as for Claude Science only, which has no `uv` and no `~/.skills-hub`.

Without that marking, agents on Claude Code read "the published skill directory" as the skill's own
folder and run `cd <skill> && python scripts/<name>.py`. The allow rules do not match that, so it prompts or is denied.

Scripts never contain credentials and never write to a data source. A script that reads data does so
with the user's own token from `~/.config/<org>/`, never from inside a package or `~/.skills-hub/`;
`check.py` warns on the literal path and the network import, and the maintainer accepts those warnings
for that script. A script that does not need data reads files or stdin and writes stdout.

Released scripts carry a sync gate that `release.py` adds after the header comments, the docstring,
and any `from __future__` imports. Your source stays as you wrote it, but tracebacks from an
installed script point 41 lines below the line in your source. Do not name anything
`_skills_hub_gate`; release refuses a script that does.
A skill that needs Sheet data says so; the Drive connector has no Sheets tools.

Skill names are unique within a package and across every package installed on one machine.
`sync`, `publish`, and `feedback` are reserved for Skills Hub.

## Draft, check, submit

```text
python framework/tools/draft.py skill --dest ~/.skills-hub/drafts/<package>/<skill> \
  --package <package> --skill <skill> --owner <email> --description "<when to use it>"
python framework/tools/check.py --package <package-dir>
```

On a user's machine the same tools are under `~/.skills-hub/framework/current/tools/`. A new
package starts from `draft.py package`. Submit with the `publish` skill, which runs `publish.py`.

## What check reports

**Blocking:** missing or invalid frontmatter; no example; no dated CHANGES.md entry; a script
without a parseable PEP 723 block; a dependency range; a Python syntax error; symlinks,
conflict copies (`name (1).py`), credential-like files, executable bits, or binaries; two skills
with the same name in one package; a reserved skill name; more than 64 files or a file over
64 KiB in one skill.

**Warnings:** imports of `socket`, `requests`, `urllib`, or `subprocess`; `eval`, `exec`, or
`os.system`; a literal path outside the working directory; any third-party dependency; a
script without `tests/`, or failing tests; a large size increase against `--baseline`.

Check does not judge prose. The maintainer reads it.

## Review

```text
python maintainer/review.py --package <dir> --skill <skill> --baseline <previous-package-dir> \
  [--drive-owner <email>] [--drive-modifier <email>]
```

The report shows the package and its maintainers, owner versus submitter, the rationale from
`submission.json`, the zip's Drive owner and last modifier, the diff against the baseline, and
the check findings.

## Decide

```text
python maintainer/decide.py inbox  --package <slug>
python maintainer/review.py --package <candidate> --skill <skill> --baseline <released package> ... > REVIEW.md
python maintainer/decide.py accept --package <slug> --zip <name>.zip --review REVIEW.md [--note "<one line for the author>"]
python maintainer/decide.py reject --package <slug> --zip <name>.zip --review REVIEW.md [--note ...]
```

`decide.py` moves the zip from `inbox/` to `accepted/` or `rejected/` under `submissions/` and uploads the
report next to it as `<name>.REVIEW.md`, so the author's agent can read the outcome. Accepting is then git: apply
the skill to the package repo, commit, bump the version, release.

## Release

```text
python maintainer/release.py --dry-run --package <dir> [--min-version <ver>] [--out dist]     # build only
python maintainer/release.py --upload  --package <dir> [--min-version <ver>] [--out dist]     # build and publish
```

Omit `--package` to build (or release) the Skills Hub zip from `framework/`. The framework tree names no real
person: `package.json` and the three framework skills carry the placeholder `r&d@example.com`, and a framework
release writes the deployment's maintainer into the zip instead (`--maintainer`, else the account in the Drive
registry); a test fails if a real address is edited into `framework/`. `--upload` puts the zip in the
package's `releases/` folder as a new immutable file (the same version twice is refused), compares
Drive's `sha256Checksum` with the local hash, and only then rewrites `current.json` in place (its file ID never
changes). A content release also writes the pointer's ID into `index.json` on the Skills Hub drive; every release
refreshes the START HERE docs. Then tag the repo (`git tag v<version>`).

## The Drive side (maintainers)

The maintainer signs in once with their own Google account: `gcloud auth login <email> --enable-gdrive-access`
(Google's own client; the Drive scope is needed to create Shared Drives). `maintainer/drive.py` takes the access
token from gcloud; nothing is stored but names and file IDs, in `~/.config/skills-hub/drives.json`.

```text
python maintainer/setup_drive.py --account <email> hub          # "Skills Hub": releases/, packages/, index.json, START HERE
python maintainer/setup_drive.py package --package <dir>        # packages/<slug>/ and packages/<slug>/submissions/; registers it in index.json
python maintainer/setup_drive.py nest                            # move packages that still have their own drives into packages/
python maintainer/setup_drive.py start-here                     # rewrite the START HERE docs with the current IDs
python maintainer/setup_drive.py share --hub --user <group or email> --role reader                 # users read
python maintainer/setup_drive.py share --package <slug> --user <group or email> --role reader
python maintainer/setup_drive.py share --package <slug> --submissions --user <group or email> --role writer  # authors submit
python maintainer/setup_drive.py share --package <slug> --user <email> --role fileOrganizer       # a package maintainer: release and review that package
python maintainer/setup_drive.py show
```

A Shared Drive's members are people or Google Groups, never a whole domain (Drive refuses it), so "everyone in
the org" is a Google Group the Workspace admin owns, added once as a reader of the Skills Hub drive. A drive member
can read every package. `--domain` only works with `--my-drive` layouts. Every command reuses what already exists
by name, so it is safe to run again. `--my-drive` builds the same layout as one folder in the account's My Drive,
for an account that may not create Shared Drives. `nest` moves an older layout (one drive per package) into
`packages/<slug>/` and deletes the empty drives.

A content release adds the sync gate to every script and refuses one that the gate pushes over 64 KiB.
Every release blocks users' scripts until they sync, so `--min-version` no longer changes what they can run.

## Feedback

```text
python maintainer/collect-feedback.py --feedback <downloaded feedback/ dir> --sheet <csv>
```

Appends files it has not seen to the CSV for the Sheet. A state file next to the CSV remembers what was collected.
