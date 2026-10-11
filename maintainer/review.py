#!/usr/bin/env python3
"""Review one skill submission.

Prints the structure report, the diff against a baseline package, the
rationale, owner versus submitter, and the Drive owner and last modifier
when those were passed in. Drive itself is not queried.

Usage:
  review.py --package DIR --skill NAME [--baseline DIR]
            [--submitter EMAIL] [--rationale TEXT]
            [--drive-owner EMAIL] [--drive-modifier EMAIL]
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "framework" / "tools"))
import check  # noqa: E402
from common import parse_frontmatter, tree_files  # noqa: E402


def main(argv):
    parser = argparse.ArgumentParser(description="Review one skill in a package directory.")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--skill", required=True, help="Skill directory name under skills/.")
    parser.add_argument("--baseline", type=Path, help="Previous package directory.")
    parser.add_argument("--submitter", help="Overrides submission.json.")
    parser.add_argument("--rationale", help="Overrides submission.json.")
    parser.add_argument("--drive-owner")
    parser.add_argument("--drive-modifier")
    args = parser.parse_args(argv)
    package_dir = args.package
    skill_dir = package_dir / "skills" / args.skill
    meta, findings = check.scan(package_dir, args.baseline)
    submission = load_submission(skill_dir)
    owner = skill_owner(skill_dir)
    submitter = args.submitter or submission.get("submitter") or "unknown"
    rationale = args.rationale or submission.get("rationale") or read_changes(skill_dir)
    print(f"package: {meta.get('package') or package_dir.name}")
    maintainers = meta.get("maintainers") or []
    print("maintainers: " + (", ".join(maintainers) if maintainers else "(none)"))
    print(f"skill: {args.skill}")
    print(f"owner: {owner}")
    print(f"submitter: {submitter}")
    print(f"rationale: {rationale}")
    print(f"drive owner: {args.drive_owner or 'unknown'}")
    print(f"drive last modifier: {args.drive_modifier or 'unknown'}")
    print("diff:")
    baseline_skill = None if args.baseline is None else args.baseline / "skills" / args.skill
    print(diff_skill(baseline_skill, skill_dir, args.skill), end="")
    for finding in findings:
        print(finding.line())
    blocking = sum(1 for finding in findings if finding.level == "blocking")
    warnings = sum(1 for finding in findings if finding.level == "warning")
    print(f"{blocking} blocking, {warnings} warnings")
    return 1 if blocking else 0


def load_submission(skill_dir):
    path = skill_dir / "submission.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def skill_owner(skill_dir):
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return "unknown"
    frontmatter, _ = parse_frontmatter(skill_file.read_text(encoding="utf-8", errors="replace"))
    return (frontmatter or {}).get("owner") or "unknown"


def read_changes(skill_dir):
    path = skill_dir / "CHANGES.md"
    if not path.is_file():
        return "none"
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text or "none"


def diff_skill(baseline, current, name):
    before = file_map(baseline)
    after = file_map(current)
    chunks = []
    for relative in sorted(set(before) | set(after)):
        old = before.get(relative)
        new = after.get(relative)
        old_text = decode(old)
        new_text = decode(new)
        if old_text is None or new_text is None:
            chunks.append(f"binary {relative}\n")
            continue
        if old_text == new_text:
            continue
        diff = difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"baseline/skills/{name}/{relative}",
            tofile=f"skills/{name}/{relative}",
        )
        chunks.append("".join(diff))
    if not chunks:
        return "(no changes)\n"
    return "".join(chunks) if chunks[-1].endswith("\n") else "".join(chunks) + "\n"


def file_map(directory):
    if directory is None or not directory.is_dir():
        return {}
    return {relative: path.read_bytes() for path, relative in tree_files(directory)}


def decode(data):
    if data is None:
        return ""
    try:
        return data.decode("utf-8")
    except UnicodeError:
        return None


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
