#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Print one reminder when any installed package was last checked over 24h ago or has an update pending.

Those are the packages whose gated scripts refuse to run.

Run by the framework's SessionStart hook. Local only; no network.

Usage:
  stale.py [--root DIR]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import DEFAULT_ROOT, HUB_SLUG, load_state, parse_time


def main(argv):
    parser = argparse.ArgumentParser(description="Remind when a package check is over 24h old or an update is pending.")
    parser.add_argument("--root", type=Path, help="Install root. Default: the root this script is installed in.")
    args = parser.parse_args(argv)
    root = (args.root or default_root()).expanduser()
    stale = stale_slugs(load_state(root), datetime.now(timezone.utc))
    if stale:
        print("sync: packages are stale and their scripts will not run until synced: " + ", ".join(stale))
    return 0


def default_root():
    parts = Path(__file__).resolve().parts
    if parts[-4:-1] == ("framework", "current", "tools"):
        return Path(*parts[:-4])
    return DEFAULT_ROOT


def stale_slugs(state, now):
    records = dict(state.get("packages", {}))
    if isinstance(state.get("framework"), dict) and "last_check" in state["framework"]:
        records[HUB_SLUG] = state["framework"]
    found = []
    for slug, record in records.items():
        checked = parse_time(record.get("last_check")) if isinstance(record, dict) else None
        if checked is None or not timedelta(0) <= now - checked <= timedelta(hours=24) or record.get("pending_version"):
            found.append(slug)
    return sorted(found)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
