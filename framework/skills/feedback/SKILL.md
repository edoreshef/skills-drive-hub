---
name: feedback
description: "Use when the user wants to record whether a skill worked, or when a Skills Hub install or sync did not go smoothly."
owner: r&d@example.com
data_sources: none
---

# feedback

Ask which package, which skill, the question, whether it worked, and an optional note. Ask for consent to write that down. If the user does not consent, stop. If they consent, run:

```text
python ~/.skills-hub/framework/current/tools/feedback.py --dest <feedback-dir> --package <package> --skill <skill> --author <email> --question "<question>" --worked yes --consent --root ~/.skills-hub
```

Use `--worked no` when it did not work. Upload the JSON file with `create_file` to that package's `feedback/` folder.

## A rough install or sync

An install or sync that was not smooth is also feedback, even if it ended well: a retry, a hash mismatch, a zip that came back inline, a `uv` install that needed a workaround, a step done differently from how START HERE or the sync skill describes it. Tell the user what went wrong in one or two sentences and offer to record it. With consent, run feedback.py with `--package skills-hub`, `--skill install` or `--skill sync`, `--version <Skills Hub version from doctor.py>` instead of `--root` (Skills Hub itself is not in `state.json`), `--worked no`, and a `--note` saying what went wrong and what was done instead. Upload the file to the foundation package's `feedback/` folder; the Skills Hub maintainers maintain that package.
