# START HERE

Source for the START HERE Google Doc on the Skills Hub drive. The user connects Google Drive,
then tells their agent: *"Read the START HERE doc on the Skills Hub drive and follow it."*
This doc is prose, so reading it with `read_file_content` is fine. Every package file is
fetched with `download_file_content`.

1. Confirm Google Drive is connected for this host.
2. Claude Code and Cursor: if `uv --version` fails, install `uv` (no admin needed). Claude Science: set the `skill_edit` and `skill_publish` grants from the host (see hosts.md).
3. Download the Skills Hub `current.json` by file ID `<SKILLS_HUB_CURRENT_JSON_ID>`, then the zip by its `zip_file_id`. A `current.json` comes back inline; read it from the decoded base64 `content`. A zip is saved by the host to a file. Never retype a zip's base64. If a zip comes back inline, stop and tell the user to add `"env": {"MAX_MCP_OUTPUT_TOKENS": "2000"}` to their Claude Code settings and start a new session.
4. The saved file is JSON. Decode its `content` field from base64 and check the sha256 of the result against `zip_sha256` (`shasum -a 256`, or `certutil -hashfile <file> SHA256`). On a mismatch, retry once, then stop.
5. Unzip into `~/.skills-hub/framework/current/`, then delete `padding.bin` from it.
6. Download `index.json` by file ID `<INDEX_JSON_ID>`. For the foundation package and each domain package the user names, download its `current.json` and zip, then run `python ~/.skills-hub/framework/current/tools/install.py --package <slug> --sha256 <zip_sha256> --bytes <zip_bytes> --version <version> --current-file-id <id> --from-tool-result <saved zip file>`.
7. Claude Code: register `~/.skills-hub` once as a local directory marketplace and add the allow rules. Cursor: run `python ~/.skills-hub/framework/current/tools/link.py`. Claude Science: publish each skill with `host.skills`.
8. Run `python ~/.skills-hub/framework/current/tools/doctor.py` and tell the user, in plain language, the Skills Hub version, each package version, and any blocked skill name.

Later updates use the `sync` skill. A package's scripts refuse to run when its last check is over 24 hours old or an update is pending; sync it, then run the script again.
