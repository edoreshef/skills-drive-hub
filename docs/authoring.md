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

## Release

```text
python maintainer/release.py --dry-run --package <dir> [--min-version <ver>] [--out dist]
```

Omit `--package` to build the Skills Hub zip from `framework/`. Upload is not implemented yet; see [`design.md`](design.md#status).

A content release adds the sync gate to every script and refuses one that the gate pushes over 64 KiB.
Every release blocks users' scripts until they sync, so `--min-version` no longer changes what they can run.

## Feedback

```text
python maintainer/collect-feedback.py --feedback <downloaded feedback/ dir> --sheet <csv>
```

Appends files it has not seen to the CSV for the Sheet. A state file next to the CSV remembers what was collected.
