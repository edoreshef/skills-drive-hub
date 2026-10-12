# Spikes

Experiments run before the framework was built. The design decisions in
[`docs/design.md`](../docs/design.md) cite these results.

Assets for rerunning them:

- `drive-kit/` — five connector-fidelity files, their `manifest.json`, and `README.md`, the prompt the agent follows. Upload the folder to Drive with "Convert uploads to Google Docs format" **off**, then tell the agent to follow the README. Regenerate the files with `python spikes/make_fixtures.py`; check a downloaded copy with `python spikes/make_fixtures.py --verify <dir>`.
- `spike-hello/` — a minimal skill whose script depends on `tabulate`. Used for loading, hook, permission, and Claude Science publish tests.
- `drive-mcp/` — a stand-in for the claude.ai Google Drive connector as a local stdio MCP server (same tool names and result shapes; auth = the maintainer's gcloud sign-in through `maintainer/drive.py`), with its `mcp.json`. For end-to-end tests of START HERE and sync on a host without the connector (S11).

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
| S10 Claude Science sync state | **Answered by S12.** A workspace-relative file is shared by kernel and shell and persists, but is not reachable by a relative path from a published skill's `scripts/`, and the published skills mount is read-only. So the state lives at `SKILLS_HUB_ROOT=<workspace>/.skills-hub` and the gate reads that variable (0.1.4). | Claude Science 0.1.60, Linux, 2026-10-11 |
| S12 agent-driven START HERE in Claude Science, real Shared Drives | **Pass**, with findings fixed in 0.1.4: all nine skills published byte-exact (39 files), hashes matched first time, doctor ok, a published script ran; 28 tool calls, 48 approval cards (all auto-allowed by the two grants), about 12 min. Found: `~` is a per-cell tmpfs; `PYTHONSAFEPATH=1` broke `python3 <abs>/install.py`; `--from-tool-result` refused raw zip bytes; the inline-zip stop rule is Claude-Code-only. | Claude Science 0.1.60, Linux, the daemon's web UI driven by Playwright, 2026-10-11 |
| S11 agent-driven START HERE and sync against real Shared Drives | **Pass.** Headless Claude Code followed the START HERE Doc end to end (13–16 tool calls, ~3 min), then the installed `sync` skill moved the foundation 0.1.2 → 0.1.3 (9 calls). Both zips saved to files at the default output limit; hashes matched first time; gated scripts ran with zero prompts under the documented allow rules and were denied without them. Found and fixed: no tool wrote `marketplace.json`; step 7 gave no commands. | Claude Code CLI 2.1.288, Linux, the first organization's Shared Drives: first through `spikes/drive-mcp`, then through the real claude.ai connector (START HERE 16 calls, 100 s; sync 6 calls), 2026-10-11 |
| S13 Cursor Drive MCP | **Pass** for the connection: Google's remote Drive MCP server (`drivemcp.googleapis.com/mcp/v1`) in `~/.cursor/mcp.json`, Local sign-in with the drives' Google account, 8 tools including the connector's five by name. **Fail:** Cursor's Google Drive plugin 1.0.1, which routes through `api.cursor.com`: `401 after successful authentication` on every attempt. Its Cloud row fails too (Google rejects Cursor's OAuth app). Fidelity and the end-to-end START HERE not run. | Cursor 3.15.6, Linux, plugin 1.0.1, 2026-10-12 |

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

## S11 — Agent-driven START HERE and sync, real Shared Drives

Setup: the framework and `<org>-foundation` released with `release.py --upload` to the Shared Drives
`setup_drive.py` made (Google Workspace, the first organization). The CLI's claude.ai login had no Drive connector, and its
Google account cannot see those drives, so `spikes/drive-mcp/server.py` stood in for the connector (same five tools,
same result shapes, `--strict-mcp-config`). Headless `claude -p --dangerously-skip-permissions`, told to read the
START HERE Doc by file ID and to use `/tmp/e2e/skills-hub` as the root.

- **Run 1 (framework 0.1.2):** steps 1–6 and 8 clean in 13 tool calls; both zips (about 87,600 characters of base64)
  were saved to files and `install.py --from-tool-result` read them; sha256 matched first time. The agent reported
  step 7 as underspecified: no `marketplace.json` existed anywhere, and no command or allow rule was given. Both were
  true: `design.md` listed `marketplace.json` but no tool wrote it. Fixed in 0.1.3 (`install.py` writes
  `<root>/.claude-plugin/marketplace.json`; START HERE step 7 gives the commands and rules).
- **Run 2 (framework 0.1.3):** 16 calls, nothing not smooth. `claude plugin marketplace add <root>` and
  `claude plugin install skills-hub@skills-hub` / `<org>-foundation@skills-hub` succeeded; `claude plugin validate`
  passed the generated marketplace file (warnings about missing author fields only). The agent noted that the plugin
  commands themselves write `extraKnownMarketplaces` and `enabledPlugins` into `~/.claude/settings.json`.
- **Loading:** a fresh session saw all nine skills (six foundation, three framework). Without allow rules every
  attempt to run or read a skill script was denied (as S7). With `Bash(uv run --script <root>/*)` and
  `Read(<root>/**)` both gated scripts ran with zero prompts; `uv` resolved the Google pins.
- **Sync:** after `<org>-foundation` 0.1.3 was released, a session running the installed `sync` skill
  downloaded `current.json` by the ID in `state.json`, was told a zip was required, downloaded it (saved to a file),
  installed 0.1.3 (`previous/` kept), ran doctor: 9 tool calls. The agent also observed, correctly, that the gate
  cannot block before a check has run: a script run just before sync still passed. That is the design.
- **Found by the agents on the way:** `identity.py` left `odd_number` null when the ODD number arrived as an alias
  (fixed, foundation 0.1.3). `publish.py` glued the CHANGES.md heading to the previous paragraph (fixed).
- **Real connector (same day):** the CLI showed no connectors because `CLAUDE_CODE_OAUTH_TOKEN` was set in the shell
  (`[claudeai-mcp] Missing user:mcp_servers scope`); with it unset, the Max login's connectors loaded, and Google Drive
  (connected at claude.ai to the drives' Google account) saw the Skills Hub drives. START HERE from scratch: 16 tool calls, about
  100 s, both zips saved to files, hashes matched first time, plugins registered. The `sync` skill: 6 calls, "up to
  date" (the download tool is deferred and needs one ToolSearch first). The agent asked for `python3` in the Doc
  (bare `python` was another project's venv on this machine): changed.
- Cleanup: `claude plugin uninstall` ×2 and `claude plugin marketplace remove skills-hub` undo the registration; the
  cache folder `~/.claude/plugins/cache/skills-hub` has to be deleted by hand (as S4 said).

## S12 — Claude Science, agent-driven START HERE

Setup: the daemon's web UI (`claude-science serve`, v0.1.60) driven headlessly with Playwright: a nonce login
(`claude-science url`), the two `customize_mutation` grants written through `PUT /api/approvals/grants` from the
UI's own origin (the daemon refuses cross-site writes and needs its `x-operon-csrf` header), then the prompt typed
into a session of the project whose Drive tool grants already existed. The Drive connector is the claude.ai one
(the maintainer's claude.ai account, Google Drive connected to the drives' Google account).

- Steps 1–8: both zips downloaded in the kernel (`download_file_content` returns a dict; no base64 reached the
  conversation), sha256 matched in the kernel and again with `shasum`, `install.py` installed the foundation,
  `host.skills.edit` ×39 and `publish` ×9 with 0 errors, doctor ok. 28 tool calls; the 48 approval cards were all
  auto-allowed by the grants.
- `identity.py` ran from the published skill directory with the "no ~/.skills-hub" warning (the gate's warn-and-run
  branch; replaced by `SKILLS_HUB_ROOT` in 0.1.4).
- Not smooth (all fixed in 0.1.4 or documented): `~` did not persist between cells, so the agent re-rooted the hub
  under the workspace; `PYTHONSAFEPATH=1` made `from common import` fail; `--from-tool-result` died on raw zip
  bytes; the "zip came back inline → stop" rule did not apply.
- **Rerun on 0.1.4 / foundation 0.2.2 (same day):** followed the Doc as written, nothing done differently. Root
  `<workspace>/.skills-hub` through `SKILLS_HUB_ROOT`, no `--root`, no `PYTHONPATH`; both hashes matched first time;
  9 stale skills deleted, 15 published (87 files, all sha256-identical to the install root); doctor ok. 111 cards,
  all auto-allowed by the `skill_edit` / `skill_publish` / `skill_delete` grants (518 s). The gate on Science: without
  the variable, warning and run; with it, silent pass; with `pending_version` set, exit 75 and the "run sync" line.
  Still true: `get_file_metadata` is not covered by the project's Drive grants and its card self-dismissed after
  10 minutes; a published skill directory is read-only.
- `/api/frames/<id>` holds the full transcript (`context_data._messages`); a session's status stays `processing`
  while it is open, so poll the last assistant message, not the status.

## S13 — Cursor Google Drive MCP

Question: which Google Drive MCP a Cursor user adds, since Cursor has no claude.ai connectors.

- **Cursor's Google Drive plugin (1.0.1) fails.** Until 2026-09-28 the plugin's `mcp.json` pointed at Google's server,
  `https://drivemcp.googleapis.com/mcp/v1`; 1.0.1 moved it to Cursor's relay, `https://api.cursor.com/rest-mcp/google-drive/mcp`
  (`cursor/plugins` PR 421). Five attempts on 2026-10-12 gave the same trace: relay answers 401 and asks for OAuth; Google
  consent completes; the callback on `localhost:8787` is received (Cursor listens there, `GET /callback` answers 200);
  `MCP OAuth callback exchange completed`, `tokens persisted` (access token, refresh token, both Drive scopes); Cursor
  refreshes the token at once (clock in sync, so not an expiry problem); the first `POST` to the relay with the Bearer
  token gets `401 {"error":"unauthorized"}`; `Auth-related error ... Server returned 401 after successful authentication`;
  state back to `needsAuth`. The UI shows "Exchanging token..." then "Authenticate". The account used makes no
  difference. The plugin's **Cloud** row fails earlier: Google shows "Access blocked: Authorization Error,
  Error 400: invalid_request" for Cursor's own OAuth app. Cursor's forum has the identical trace for the Atlassian
  plugin, escalated by staff without a fix date; the documented clean sign-in (Logout under Environments > Local,
  restart, Authenticate) did not help there.
- **Google's own server passes.** `{"type": "http", "url": "https://drivemcp.googleapis.com/mcp/v1"}` under
  `mcpServers` in `~/.cursor/mcp.json`. Cursor loaded it within seconds (no restart), marked it `needsAuth` with
  `Static-client server connected without stored tokens; interactive OAuth required`, and Authenticate on the Local
  row opened Google's consent. Signed in with the Google account that is a member of the drives, which is not the
  Cursor account; the callback was received and the entry connected. The server's
  `/.well-known/oauth-protected-resource/mcp/v1` names `accounts.google.com` as the authorization server and
  offers scopes `drive`, `drive.readonly`, `drive.file`. Unauthenticated `initialize` and `tools/list` succeed; only
  tool calls need the token.
- **Tool surface:** 8 tools: `search_files`, `get_file_metadata`, `read_file_content`, `download_file_content`,
  `create_file` (the connector's five, same names), `copy_file`, `get_file_permissions`, `list_recent_files`.
  `download_file_content` is described as base64 of the file, as the connector's is.
- Naming: with the plugin enabled, the settings list shows two entries called `google-drive`, and a sign-in started from
  the plugin's entry goes through the relay. The direct entry is therefore named `google-drive-direct`, and the plugin
  is disabled.

Open: byte-exactness of `download_file_content` on Google's server (repeat S1), and an agent-driven START HERE and sync
in Cursor (repeat S11). Tested on Cursor 3.15.6, Linux, 2026-10-12.
