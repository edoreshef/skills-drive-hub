---
name: shared-terms
description: "Fixture skill. Use only when the user says the exact phrase 'run shared terms'."
owner: r&d@example.com
data_sources: none
---

# shared-terms

When triggered:

1. Reply with the marker `SHARED-TERMS-SKILL-LOADED`.
2. Run exactly this command and report its output verbatim:

```text
uv run --script ~/.skills-hub/packages/foundation-sample/current/skills/shared-terms/scripts/echo_marker.py
```

Run it as written, from any directory. Do not `cd` first, do not call `python` on the script, and do not swap in another path: the permission rules allow only this command.

Only on Claude Science, which has no `uv` and no `~/.skills-hub`: there are no dependencies to install. From the published skill directory, run `python scripts/echo_marker.py`. Use that directory's path, not `~`.
