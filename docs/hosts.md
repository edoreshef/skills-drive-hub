# Hosts

How each host loads packages and runs scripts. Tested versions are in
[`spikes/README.md`](../spikes/README.md).

## Claude Code

Drive: the claude.ai Google Drive connector, tied to the user's claude.ai account.

Register `~/.skills-hub` once as a local directory marketplace. No git and no network:

```text
claude plugin marketplace add ~/.skills-hub
claude plugin install <plugin> --marketplace <name>
```

`marketplace.json` lists `framework/current` and each `packages/<slug>/current`. Sessions read
those directories in place, so swapping `current` is the update. Do not also copy these skills
into `~/.claude/skills`: they would load twice. `claude plugin marketplace remove` leaves a
cache folder under `~/.claude/plugins/cache/`; delete it on uninstall.

The `skills-hub` plugin's SessionStart hook runs `stale.py` without a prompt. If it prints a reminder, run the `sync` skill.

Released scripts carry the sync gate ([`design.md`](design.md#the-sync-gate)). A script whose package
was checked over 24 hours ago, or has an update pending, exits 75 with a line telling the agent to
run sync. The gate reads `~/.skills-hub/state.json` even when a script runs from Claude Code's plugin cache.

A skill script is one absolute command, with no `cd` and no check for `uv` first:

```text
uv run --script ~/.skills-hub/packages/<slug>/current/skills/<skill>/scripts/<name>.py
```

With these user-level allow rules that runs with no prompts (Windows: `%USERPROFILE%\.skills-hub\…`):

```text
Bash(uv run --script ~/.skills-hub/*)
Bash(uv run --script <absolute home>/.skills-hub/*)
Read(~/.skills-hub/**)
```

If the agent composes its own command instead, the rules stop matching. Rules for the writes sync makes under `~/.skills-hub` have not been measured.

## Cursor

Drive: Cursor has no claude.ai connectors. It needs a remote Google Drive MCP, not chosen yet.

Cursor reads `~/.claude/skills` and `~/.cursor/skills`, follows symlinks, and loads nested skill folders. Link every installed package with:

```text
python ~/.skills-hub/framework/current/tools/link.py --root ~/.skills-hub
```

That creates `~/.cursor/skills/<slug>` pointing at the package's `current/` (a junction on
Windows). `links.json` records which links `link.py` created; it never touches other entries,
and `--unlink <slug>` removes only that package's link. A skill that `doctor.py` blocks is left
out of the incoming package's link.

Script commands are the same as Claude Code. Cursor's command allowlist has not been measured.
Whether a `sessionStart` hook can add text to the agent is untested, so users run sync when versions look old.
The sync gate works the same as on Claude Code: the script resolves the `~/.cursor/skills/<slug>` link to
`~/.skills-hub` and blocks when the package is stale. Until a Drive MCP is chosen, a blocked Cursor user
cannot sync from Cursor; only a host with the Drive connector, such as Claude Code on the same
machine, can unblock them.

## Claude Science

Drive: the claude.ai Google Drive connector. Connect it at `claude.ai/customize/connectors`
while signed into the same claude.ai account. Once connected it is attached to the main agent
profile. Each Drive tool asks once; choose "Allow for this project" or turn on the connector's
"Skip approvals".

Claude Science does not read `~/.skills-hub` or `~/.claude/skills`; its sandbox has its own home.
The install path is different:

1. Before the first install, write two standing grants from the host, once per machine:
   `PUT /api/approvals/grants` with `{kind: "customize_mutation", key: "skill_edit" | "skill_publish", tier: "allow"}`.
   Without them every file edit and every publish shows an approval card. Do not use
   `--dangerously-skip-approvals`: it also auto-approves code, network, and host files.
2. Download the zip in the Python kernel and check sha256 there. The payload never enters the conversation.
3. `host.skills.edit` each file, then `host.skills.publish` each skill.

A published skill is stored on the claude.ai account and does not appear in Claude Code.
Publish limits: at most 64 files per skill, 64 KiB per file, no binaries, valid frontmatter.
The catalog is flat, so skill names must be unique across every installed package.

Scripts: there is no `uv`. Install each declared dependency with `manage_packages` (a bare
name or an exact `==` pin; ranges are rejected), then `python scripts/<name>.py` from the
published skill directory. Installs go to the shared environment. The Python kernel and the
shell have different home directories, so use workspace-relative paths, not `~`.

There is no SessionStart hook. Users run sync when versions look old.

The sync gate cannot check anything here: the sandbox has no `~/.skills-hub`. Until spike S10 settles
where Science keeps sync state, gated scripts print a warning and run.

On Ubuntu 24.04 the sandbox needs an AppArmor profile that grants `userns` to `/usr/bin/bwrap`.
