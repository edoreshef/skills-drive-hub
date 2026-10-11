---
name: __SKILL__
description: "__DESCRIPTION__"
owner: __OWNER__
data_sources: none
---

# __SKILL__

When triggered, run exactly this command and report its output verbatim:

```text
uv run --script ~/.skills-hub/packages/__PACKAGE__/current/skills/__SKILL__/scripts/run.py
```

Run it as written, from any directory. Do not `cd` first, do not call `python` on the script, and do not swap in another path: the permission rules allow only this command.

Only on Claude Science, which has no `uv` and no `~/.skills-hub`: there are no dependencies to install. From the published skill directory, run `python scripts/run.py`. Use that directory's path, not `~`.
