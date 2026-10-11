# Spikes

Experiments run before the framework was built. The design decisions in
[`docs/design.md`](../docs/design.md) cite these results.

Assets for rerunning them:

- `drive-kit/` — five connector-fidelity files, their `manifest.json`, and `README.md`, the prompt the agent follows. Upload the folder to Drive with "Convert uploads to Google Docs format" **off**, then tell the agent to follow the README. Regenerate the files with `python spikes/make_fixtures.py`; check a downloaded copy with `python spikes/make_fixtures.py --verify <dir>`.
- `spike-hello/` — a minimal skill whose script depends on `tabulate`. Used for loading, hook, permission, and Claude Science publish tests.

Record new results here with host, version, OS, Drive type, and date.

Results recorded before 2026-10-11 use the old install root, `~/.ai-dist` (now `~/.skills-hub`),
and the old framework plugin name, `framework` (now `skills-hub`).

## Results

| Spike | Result | Tested on |
|---|---|---|
| S1 connector fidelity | **Pass** with `download_file_content` (byte-exact). `read_file_content` mismatched every file. | Claude Code in the desktop app, macOS 26.6, Shared Drive. Claude Science 0.1.60, Linux, My Drive. |
| S2 connector writes | `create_file` with base64 is byte-exact. `update_file` changes only title and parent. | Same as S1 |
| S3 Claude Science | **Pass**, with its own install path (`host.skills`), own Python, and two grants that remove approval cards. | 0.1.60, Linux |
| S4 Claude Code marketplace | **Pass.** Loads in place; a directory swap is the update; SessionStart hook runs. Tested with one plugin. | Claude Code 2.1.288, Linux |
| S5 Cursor | Skill loading **passes** (symlinks, nested folders, both skill dirs). `sessionStart` output not verified. | Cursor, Linux |
| S6 uv | **Pass** on Linux. macOS, Windows, proxy not tested. | uv 0.10.0, Linux |
| S7 permissions | **Pass.** Zero prompts with the allow rules and one absolute command. | Claude Code 2.1.288, Linux |
| S8 Drive checksums | **Pass** on My Drive: upload returns `sha256Checksum` and it matched. Shared Drive and rclone not tested. | Drive API v3, Linux |
| S9 install and sync through the connector | **Pass** at the default limit with zips padded to 64 KiB, and with `MAX_MCP_OUTPUT_TOKENS=2000`. **Fail** at the default without padding: a 26 KB zip came back inline and the model's copy of it was wrong. | Claude Code CLI 2.1.288, Linux, My Drive, 2026-10-10 |
| S10 Claude Science sync state | **Not run.** Procedure below. Until it runs, gated scripts on Science warn and run. | — |

## S1, S2 — Google Drive connector (claude.ai)

| File | Bytes | `read_file_content` | `download_file_content` |
|---|---|---|---|
| tricky.py | 230 | 264, mismatch | match |
| tricky.md | 170 | 195, mismatch | match |
| tricky.json | 130 | 125, mismatch | match |
| crlf.txt | 31 | 33, mismatch | match |
| large.py | 50,670 | 53,069, mismatch | match |

Both hosts gave the same result.

- `read_file_content` returns Markdown, not the file. It escapes `# * _ [ ]` and backticks, adds two trailing spaces per line, collapses tabs, converts CRLF to LF, and drops the final newline. It does not truncate.
- `download_file_content` returns JSON `{content, id, mimeType, title}` with `content` as base64 of the raw bytes.
- **Claude Code** saved the large result (about 67 KB of base64) to a local tool-results file instead of the conversation, and the agent decoded it from there. Small results came back inline and the model copied the base64 into a file; that still matched, but it is model copying. Four small files cost about 4–5k tokens.
- **Claude Science** calls connectors from its Python kernel, so the result arrived as a Python value and only sizes and hashes reached the conversation.
- `create_file` (base64, conversion off) round-tripped exactly, including a tab, trailing spaces, and Hebrew. `update_file` takes only `fileId`, `title`, and `parentId`; passing content gives HTTP 400. A new version is a new file.
- Folder listings paginate: one file only appeared on the second page. Address files by ID.
- The connector has no Sheets tools.

Open: the largest zip one call can return, and the size at which Claude Code spills to a file.

## S3 — Claude Science

- It does not read `~/.claude/skills`. The sandbox has its own home, and skills live in a catalog managed through the `host.skills` SDK (`list`, `read`, `edit`, `publish`, `delete`) in its `repl` tool. Origins: bundled (read-only), personal or organization (published), draft.
- **Drive** comes from the claude.ai account's connector. Claude Science's Connect button opens `claude.ai/customize/connectors`; once connected there, Drive is attached to the main agent profile within a minute. Each Drive tool asks once. Version 0.1.47 showed an "on" switch for a connector that was never authorized (calls failed with `unknown server`); 0.1.60 shows a Connect button instead.
- **Install:** download in the kernel, check sha256, `host.skills.edit` per file, `host.skills.publish`. Files matched the zip byte for byte. Extra frontmatter keys (`owner`, `data_sources`) were accepted.
- **Approval cards:** each edit and each publish showed an "Allow once" card, so cards scale with file count. The same card offers "This project" and "Global", keyed by call type, not by skill. Writing both grants with `PUT /api/approvals/grants` (`kind: customize_mutation`, `key: skill_edit | skill_publish`, `tier: allow`) stores scope `always`; an edit plus publish then finished in 2.5 s with no card. The PUT was made from the signed-in web page; calling it from inside the sandbox is untested.
- **Publish** stores the skill on the claude.ai account. It did not appear in Claude Code (`claude -p`, same account). claude.ai web and Claude Desktop were not checked.
- Publish limits: 64 files per skill, 64 KiB per edit, no binaries, valid frontmatter YAML.
- **Scripts:** no `uv`. `python scripts/hello.py` ran but ignored the PEP 723 block. `manage_packages(mode="install", environment="python", packages=["tabulate"], use_pip=True)` installed it in about 10 s into the shared environment, which accepts bare names or `==` pins only.
- The Python kernel and the shell sandbox have different home directories. Use workspace-relative paths.
- Ubuntu 24.04 needs an AppArmor profile for `/usr/bin/bwrap` granting `userns`.
- Rejected install paths: "Upload a skill" (manual, one zip per skill) and "Import from GitHub" (needs a GitHub repo; no sign-in for private repos). Neither updates on its own.

## S4 — Claude Code local directory marketplace

Setup: a directory with `.claude-plugin/marketplace.json` listing one relative path `./lib/current`, holding a plugin with one skill and a SessionStart hook.

- `claude plugin validate`, `marketplace add <dir>`, and `install` work with no git and no network.
- Sessions read the skill from the marketplace directory, although Claude Code also writes a copy under `~/.claude/plugins/cache/`.
- Renaming `current → previous` and `staging → current` was picked up by the next session, with no update command or version bump.
- The hook `uv run --script "${CLAUDE_PLUGIN_ROOT}/tools/stale.py"` ran without a prompt, and its output reached the agent.
- The same skill in `~/.claude/skills/` and in the plugin loads twice (`spike-hello` and `<plugin>:spike-hello`).
- `marketplace remove` uninstalls the plugin but leaves the cache folder.

## S5 — Cursor

Cursor's loaded skill list included skills from both `~/.claude/skills/` and `~/.cursor/skills/`,
including nested `skills/*/SKILL.md` reached through a symlinked folder. Open: whether a
user-level `sessionStart` hook (`~/.cursor/hooks.json`) can add text to the agent's context.

## S7 — Claude Code permissions

- Without allow rules: six permission denials in a headless run (reading the script, `command -v uv`, three ways of running it), and the agent wrapped commands as `cd … && …`.
- With `Bash(uv run --script ~/.ai-dist/*)`, the same rule with the home path expanded, and `Read(~/.ai-dist/**)`, plus a SKILL.md line giving one exact absolute command: zero denials.
- `uv` resolved the PEP 723 dependency into its cache on first run.

## S8 — Drive checksums

A Drive API v3 multipart upload returned `sha256Checksum` for every file, and all six matched the local hashes.

## S9 — Install and sync through the connector

Setup: the framework and three packages released to a My Drive folder through the Drive API, with
`current.json` rewritten in place on each release. Headless `claude -p` sessions followed
`docs/start-here.md`, then the installed sync skill, against a scratch install root. The CLI has the
claude.ai connector only when signed in with a claude.ai login; a `CLAUDE_CODE_OAUTH_TOKEN` setup
token does not carry it.

| Result | Characters | Default limit | `MAX_MCP_OUTPUT_TOKENS=2000` |
|---|---|---|---|
| `current.json` | about 470 | inline | inline |
| 2–3 KB zip | about 3,700 | inline | inline |
| 26 KB framework zip | 35,530 | inline | saved to a file |
| 235 KB zip | 313,125 | saved to a file | saved to a file |

- A saved result is the raw JSON `{content, id, mimeType, title}` under `~/.claude/projects/<project>/<session>/tool-results/`. The tool result says `Error: result (N characters) exceeds maximum allowed tokens. Output has been saved to <path>`, and the agent passes that path on. `install.py --from-tool-result` and `sync.py` read it directly, and `sync.py` records `current_file_id` from its `id`.
- Default limit: the model retyped the inline 35,530-character framework zip into a file. That took about 17 minutes, and the copy was wrong: 33,986 characters, diverging at byte 11,233. The connector's own bytes matched `zip_sha256`; only the copy failed. The hash check would have refused it.
- With the limit at 2000: the full START HERE install (framework and three packages) took about 2 minutes, and sync of two bumped packages took about 3.5 minutes. Installed versions, hashes, and `current_file_id` all matched Drive. The small inline results were retyped correctly in this run.
- A `current.json` rewritten with a Drive API media update was read at its new version by the next session.
- Threshold at the default limit, measured with random files of 18 sizes: a result of 49,982 characters came back inline, and one of 50,050 characters was saved to a file. Every size below came back inline and every size above was saved. A zip is saved once it is over about 37.4 KB.
- Padded to 64 KiB (`release.py`), every zip was about 87,600 characters and was saved to a file at the default limit. Install of the framework and three packages took about 2 minutes, and sync of two bumped packages took about 2 minutes. Both matched Drive. The agent deleted the framework's `padding.bin`, and `install.py` left it out of each package.
- `MAX_MCP_OUTPUT_TOKENS` set through the settings `env` block (`--settings`) works the same as the environment variable: the 35,530-character result was saved to a file.

Open: the largest result one call can return (313,125 characters worked), and the same measurement in the desktop app.

## S10 — Claude Science sync state

Question: can Science keep one sync-state file, written when sync checks a package, that every
published skill's scripts can read, in later sessions too? If yes, that file is Science's
`state.json` and the gate fails closed there. If no, the only other way to keep the gate is to
republish every skill on each check.

1. In the Python kernel, write `skills-hub/state.json` relative to the workspace, holding one fresh package record. Note the absolute path the kernel resolved.
2. From the shell sandbox, read the same relative path. The kernel and the shell have different home directories (S3), so check both see the file.
3. Publish a skill whose script prints `Path(__file__).resolve()`, `Path.cwd()`, and whether the file from step 1 is readable from there. Run it with `python scripts/<name>.py` from the published skill directory.
4. Start a new session, or restart Claude Science, and repeat step 3. The file must still be there and readable.
5. Repeat step 3 from a second project, to see whether the file is per project or per workspace.

Record the host version, OS, each resolved path, and whether the file survived. If it passes,
change the gate's "no `~/.skills-hub`" branch to read that path and fail closed.
