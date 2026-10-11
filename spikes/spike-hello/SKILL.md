---
name: spike-hello
description: "Spike test skill. Use only when the user says the exact phrase 'run spike hello'."
owner: maintainer
data_sources: none
---

# spike-hello

When triggered:

1. Reply with the marker `SPIKE-HELLO-SKILL-LOADED`.
2. Run the script in this skill's `scripts/` folder: first try `uv run --script scripts/hello.py`; if `uv` is not available, run `python scripts/hello.py`.
3. Report the script's full output verbatim, plus the exact command and working directory you used.
