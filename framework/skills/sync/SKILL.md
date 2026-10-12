---
name: sync
description: "Use when the user says sync, when a session reminder says packages are stale, or when a skill script prints 'blocked: package ... Run the sync skill'."
owner: r&d@example.com
data_sources: none
---

# sync

For each installed package, download that package's `current.json` with `download_file_content`, by the `current_file_id` in `~/.skills-hub/state.json`. Then run:

```text
python3 ~/.skills-hub/framework/current/tools/sync.py --root ~/.skills-hub --current <current.json download>
```

A `current.json` comes back inline: write its base64 `content` to a file and pass that. If it says the package is up to date, stop there for that package. Otherwise download the zip by `zip_file_id` the same way and run it again with `--zip <zip download>`, passing the file the host saved the result to. `sync.py` decodes both forms.

Never retype a zip's base64. If a zip comes back inline in Claude Code, stop and tell the user to add `"env": {"MAX_MCP_OUTPUT_TOKENS": "2000"}` to their Claude Code settings and start a new session.

A local dry-run directory works too: `--from-release <dir>`. If sync says the package is below `min_version`, finish the sync before using that package's skills. Then run:

```text
python3 ~/.skills-hub/framework/current/tools/doctor.py --root ~/.skills-hub
```

On Cursor, then run:

```text
python3 ~/.skills-hub/framework/current/tools/link.py --root ~/.skills-hub
```

On Claude Science, `~/.skills-hub` means the workspace root in `SKILLS_HUB_ROOT` (START HERE); downloads arrive in the kernel, so decode `content` there and write the bytes to a file. After a package changed, republish its changed skills with `host.skills` (`edit` each file, then `publish`): the published copies are read-only and do not follow the install root.

If `python3 --version` does not print Python 3.9 or later, or on a Mac where `xcode-select -p` fails (there `python3` opens an install dialog; never run it), run each command above as `uv run --python-preference only-managed --script <tool>.py` with the same arguments.

Report the doctor output. Use the downloaded files. Do not retype the zip.
