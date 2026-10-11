#!/usr/bin/env python3
"""Record a decision on a submission: move its zip from inbox/ to accepted/ or rejected/ and put a REVIEW.md
next to it (design.md "Contribution", step 4). Committing an accepted skill to the package repo and releasing it
are separate steps the maintainer does with git and release.py.

Usage:
  decide.py inbox   --package SLUG                                        list the inbox
  decide.py accept  --package SLUG --zip NAME --review FILE [--note TEXT]
  decide.py reject  --package SLUG --zip NAME --review FILE [--note TEXT]

REVIEW.md is the review.py report (saved to a file), with the decision and an optional note added on top. It is
uploaded as "<zip name without .zip>.REVIEW.md" into the same folder as the moved zip, so the author's agent can
read the outcome through the connector.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive import Drive, DriveError, load_registry  # noqa: E402


def main(argv):
    parser = argparse.ArgumentParser(description="Accept or reject a submission on Drive.")
    parser.add_argument("cmd", choices=("inbox", "accept", "reject"))
    parser.add_argument("--package", required=True, help="package slug")
    parser.add_argument("--zip", help="the submission's file name in inbox/")
    parser.add_argument("--review", type=Path, help="the saved review.py report")
    parser.add_argument("--note", default="", help="one line for the author")
    parser.add_argument("--account")
    args = parser.parse_args(argv)
    registry = load_registry()
    try:
        sub = registry["packages"][args.package]["submissions"]
    except KeyError:
        print(f"error: no Drive set up for {args.package}: run setup_drive.py package", file=sys.stderr)
        return 1
    drive = Drive(args.account or registry.get("account"))
    try:
        inbox = drive.children(sub["inbox"])
        if args.cmd == "inbox":
            for f in sorted(inbox, key=lambda f: f["name"]):
                print(f"{f['name']}  {f['id']}  {f.get('size')} bytes  modified {f.get('modifiedTime')}")
            if not inbox:
                print("inbox is empty")
            return 0
        if not args.zip or not args.review:
            print("error: accept/reject need --zip and --review", file=sys.stderr)
            return 1
        match = [f for f in inbox if f["name"] == args.zip]
        if len(match) != 1:
            print(f"error: {len(match)} files named {args.zip} in inbox/", file=sys.stderr)
            return 1
        dest = sub["accepted" if args.cmd == "accept" else "rejected"]
        when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        head = (f"# Review: {args.zip}\n\n**Decision: {args.cmd.upper()}ED** ({when}, by {drive.about()['user']['emailAddress']})\n\n"
                + (f"{args.note}\n\n" if args.note else "") + "---\n\n")
        review = drive.upload(args.zip[:-4] + ".REVIEW.md", dest, (head + args.review.read_text(encoding="utf-8")).encode("utf-8"),
                              "text/markdown")
        moved = drive.move(match[0]["id"], sub["inbox"], dest)
        print(f"{args.cmd}ed {args.zip}: moved to {args.cmd}ed/ ({moved['id']}); review {review['id']}")
        if args.cmd == "accept":
            print("next: apply the skill to the package repo, commit, bump the version, release.py --upload")
    except DriveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
