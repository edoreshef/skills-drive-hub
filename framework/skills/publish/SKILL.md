---
name: publish
description: "Use when the user wants to submit a skill to a package."
owner: r&d@example.com
data_sources: none
---

# publish

Ask why the skill changed. Then run:

```text
python3 ~/.skills-hub/framework/current/tools/publish.py --package-dir <package-dir> --skill <skill> --rationale "<why>" --author <email> --out <inbox>
```

If `python3 --version` does not print Python 3.9 or later, or on a Mac where `xcode-select -p` fails (there `python3` opens an install dialog; never run it), run it as `uv run --python-preference only-managed --script <tool>.py` with the same arguments.

If it refuses, show the report and stop. If it prints a zip path, upload that zip with `create_file` to the package's inbox. Download it back and compare sha256 to the printed hash. One retry on mismatch.
