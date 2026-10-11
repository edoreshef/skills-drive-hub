---
name: publish
description: "Use when the user wants to submit a skill to a package."
owner: r&d@example.com
data_sources: none
---

# publish

Ask why the skill changed. Then run:

```text
python ~/.skills-hub/framework/current/tools/publish.py --package-dir <package-dir> --skill <skill> --rationale "<why>" --author <email> --out <inbox>
```

If it refuses, show the report and stop. If it prints a zip path, upload that zip with `create_file` to the package's inbox. Download it back and compare sha256 to the printed hash. One retry on mismatch.
