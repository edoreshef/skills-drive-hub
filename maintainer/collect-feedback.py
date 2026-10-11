#!/usr/bin/env python3
"""Append new feedback files to a CSV the maintainer imports into the Sheet.

Files already collected are skipped. The connector cannot append Sheet rows.

Usage:
  collect-feedback.py --feedback DIR --sheet CSV
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["collected_at", "file", "package", "skill", "version", "author", "question", "worked", "note"]


def main(argv):
    parser = argparse.ArgumentParser(description="Append new feedback JSON files to a CSV.")
    parser.add_argument("--feedback", required=True, type=Path)
    parser.add_argument("--sheet", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.feedback.is_dir():
        print(f"refusing collect: {args.feedback} is missing", file=sys.stderr)
        return 1
    state_path = args.sheet.with_suffix(args.sheet.suffix + ".state.json")
    seen = load_seen(state_path)
    rows = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for path in sorted(args.feedback.rglob("*.json")):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"skipping {path}: not JSON", file=sys.stderr)
            continue
        if not isinstance(payload, dict):
            print(f"skipping {path}: not an object", file=sys.stderr)
            continue
        rows.append(
            {
                "collected_at": now,
                "file": path.name,
                "package": payload.get("package", ""),
                "skill": payload.get("skill", ""),
                "version": payload.get("version", ""),
                "author": payload.get("author", ""),
                "question": payload.get("question", ""),
                "worked": "yes" if payload.get("worked") is True else "no" if payload.get("worked") is False else "",
                "note": payload.get("note", ""),
            }
        )
        seen[digest] = path.name
    append_rows(args.sheet, rows)
    save_seen(state_path, seen)
    print(f"added {len(rows)}")
    return 0


def load_seen(path):
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else {}


def save_seen(path, seen):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"files": seen}, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_rows(sheet, rows):
    sheet.parent.mkdir(parents=True, exist_ok=True)
    new_file = not sheet.exists() or sheet.stat().st_size == 0
    with sheet.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
