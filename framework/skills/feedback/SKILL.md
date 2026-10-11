---
name: feedback
description: "Use when the user wants to record whether a skill worked."
owner: r&d@example.com
data_sources: none
---

# feedback

Ask which package, which skill, the question, whether it worked, and an optional note. Ask for consent to write that down. If the user does not consent, stop. If they consent, run:

```text
python ~/.skills-hub/framework/current/tools/feedback.py --dest <feedback-dir> --package <package> --skill <skill> --author <email> --question "<question>" --worked yes --consent --root ~/.skills-hub
```

Use `--worked no` when it did not work. Upload the JSON file with `create_file` to that package's `feedback/` folder.
