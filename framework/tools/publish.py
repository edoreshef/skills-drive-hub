#!/usr/bin/env python3
"""Package one skill for submission.

Runs the structure check first. On success, records the rationale in CHANGES.md
and submission.json and writes an inbox zip. Uploading the zip is a connector
create_file, not this tool.

Usage:
  publish.py --package-dir DIR --skill NAME --rationale TEXT --author EMAIL --out DIR
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # PYTHONSAFEPATH-proof: common.py lives next to this file
import check  # noqa: E402
from common import author_token, tree_files, unique_path, write_zip


def main(argv):
    parser = argparse.ArgumentParser(description="Zip one skill after the structure check passes.")
    parser.add_argument("--package-dir", required=True, type=Path)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--out", required=True, type=Path, help="Inbox directory for the zip.")
    args = parser.parse_args(argv)
    package_dir = args.package_dir
    skill_dir = package_dir / "skills" / args.skill
    if not skill_dir.is_dir():
        print(f"refusing publish: {skill_dir} is missing", file=sys.stderr)
        return 1
    rationale = args.rationale.strip()
    if not rationale:
        print("refusing publish: rationale is empty", file=sys.stderr)
        return 1
    meta, findings = check.scan(package_dir)
    for finding in findings:
        print(finding.line(), file=sys.stderr)
    if any(finding.level == "blocking" for finding in findings):
        print("refusing publish", file=sys.stderr)
        return 1
    slug = meta.get("package")
    if not slug:
        print("refusing publish: package.json has no package", file=sys.stderr)
        return 1
    today = datetime.now(timezone.utc).date().isoformat()
    changes = skill_dir / "CHANGES.md"
    entry = f"\n\n## {today}\n\n{rationale}\n"      # rstrip above drops the file's trailing newline: put back a blank line
    changes.write_text(changes.read_text(encoding="utf-8").rstrip() + entry, encoding="utf-8")
    submission = {
        "package": slug,
        "skill": args.skill,
        "submitter": args.author,
        "rationale": rationale,
    }
    (skill_dir / "submission.json").write_text(json.dumps(submission, indent=2) + "\n", encoding="utf-8")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    name = f"{args.skill}__{stamp}__{author_token(args.author)}.zip"
    args.out.mkdir(parents=True, exist_ok=True)
    zip_path = unique_path(args.out / name)
    write_zip(zip_path, [(relative, path.read_bytes()) for path, relative in tree_files(skill_dir)])
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(
        f"submission package={slug} skill={args.skill} sha256={digest} "
        f"bytes={zip_path.stat().st_size} zip={zip_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
