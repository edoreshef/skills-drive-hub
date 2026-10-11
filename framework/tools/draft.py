#!/usr/bin/env python3
"""Copy a package or skill template and fill its placeholders.

Usage:
  draft.py package --dest DIR --package SLUG --title TITLE --maintainer EMAIL
  draft.py skill --dest DIR --package SLUG --skill NAME --owner EMAIL --description TEXT
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from common import tree_files

PLACEHOLDER = re.compile(r"__[A-Z]+__")


def main(argv):
    parser = argparse.ArgumentParser(description="Fill a package or skill template.")
    sub = parser.add_subparsers(dest="kind", required=True)
    package = sub.add_parser("package")
    package.add_argument("--dest", required=True, type=Path)
    package.add_argument("--package", required=True)
    package.add_argument("--title", required=True)
    package.add_argument("--maintainer", required=True)
    package.add_argument("--version", default="0.1.0")
    skill = sub.add_parser("skill")
    skill.add_argument("--dest", required=True, type=Path)
    skill.add_argument("--package", required=True)
    skill.add_argument("--skill", required=True)
    skill.add_argument("--owner", required=True)
    skill.add_argument("--description", required=True)
    args = parser.parse_args(argv)
    if args.kind == "package":
        values = {
            "__PACKAGE__": args.package,
            "__TITLE__": args.title,
            "__MAINTAINER__": args.maintainer,
            "__VERSION__": args.version,
            "__DATE__": date.today().isoformat(),
        }
        source = templates_root() / "package"
    else:
        values = {
            "__PACKAGE__": args.package,
            "__SKILL__": args.skill,
            "__OWNER__": args.owner,
            "__DESCRIPTION__": args.description,
            "__DATE__": date.today().isoformat(),
        }
        source = templates_root() / "skill"
    if args.dest.exists():
        print(f"refusing draft: {args.dest} already exists", file=sys.stderr)
        return 1
    copy_tree(source, args.dest, values)
    print(f"drafted {args.kind} {args.dest}")
    return 0


def templates_root():
    return Path(__file__).resolve().parents[1] / "templates"


def copy_tree(source, dest, values):
    for path, relative in tree_files(source):
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace(key, value)
        leftover = PLACEHOLDER.search(text)
        if leftover:
            raise SystemExit(f"template {relative} still contains {leftover.group()}")
        target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
