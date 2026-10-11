#!/usr/bin/env python3
"""Write one feedback file after the user consents.

The file is local. Putting it on the package's feedback drive is a connector
create_file. Without --consent this writes nothing.

Usage:
  feedback.py --dest DIR --package SLUG --skill NAME --author EMAIL
              --question TEXT --worked yes|no [--note TEXT] --consent
              [--version VER | --root DIR]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))  # PYTHONSAFEPATH-proof: common.py lives next to this file
from common import author_token, installed_version, unique_path


def main(argv):
    parser = argparse.ArgumentParser(description="Write one feedback JSON file.")
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--package", required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--worked", required=True, choices=("yes", "no"))
    parser.add_argument("--note", default="")
    parser.add_argument("--consent", action="store_true")
    parser.add_argument("--version")
    parser.add_argument("--root", type=Path, help="Read the installed version from state.json.")
    args = parser.parse_args(argv)
    if not args.consent:
        print("refusing feedback: consent required", file=sys.stderr)
        print("nothing written", file=sys.stderr)
        return 1
    version = args.version or (args.root and installed_version(args.root.expanduser(), args.package))
    if not version:
        print("refusing feedback: version is unknown", file=sys.stderr)
        print("nothing written", file=sys.stderr)
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    name = f"{stamp}__{author_token(args.author)}__{args.skill}.json"
    args.dest.mkdir(parents=True, exist_ok=True)
    path = unique_path(args.dest / name)
    payload = {
        "package": args.package,
        "skill": args.skill,
        "version": version,
        "author": args.author,
        "question": args.question,
        "worked": args.worked == "yes",
        "note": args.note,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"feedback file={path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
