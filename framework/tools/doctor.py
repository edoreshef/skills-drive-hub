#!/usr/bin/env python3
"""Report installed packages and block a skill name owned by two of them.

The incoming package is the one with the later last_check. Its copy of the
skill is reported as blocked. The other package is left as it was.

Usage:
  doctor.py [--root DIR]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))  # PYTHONSAFEPATH-proof: common.py lives next to this file
from common import DEFAULT_ROOT, HUB_SLUG, load_state, parse_time, skill_name


def main(argv):
    parser = argparse.ArgumentParser(description="Report installed packages and skill-name collisions.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Install root. Default: ~/.skills-hub")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    framework = root / "framework" / "current" / "package.json"
    if framework.is_file():
        print(f"{HUB_SLUG}: {describe(framework)}")
    else:
        print(f"{HUB_SLUG}: not installed")
    for slug, current in installed_packages(root).items():
        print(f"package {slug} {describe(current / 'package.json')}")
    found = collisions(root)
    for item in found:
        print(f"collision: {item['skill']} loaded from {', '.join(item['loaded'])}")
        print(f"blocked: {item['incoming']} {item['skill']}")
    if not found:
        print("ok")
    return 1 if found else 0


def describe(meta_path):
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    maintainers = meta.get("maintainers")
    names = ", ".join(map(str, maintainers)) if isinstance(maintainers, list) and maintainers else "(none)"
    return f"{meta.get('version')} maintainers {names}"


def installed_packages(root):
    """slug -> current/ for every package with a package.json."""
    packages = root / "packages"
    if not packages.is_dir():
        return {}
    return {
        path.name: path / "current"
        for path in sorted(packages.iterdir())
        if (path / "current" / "package.json").is_file()
    }


def blocked_skill_names(root):
    """Incoming package slug -> skill names that must not be activated."""
    found = {}
    for item in collisions(root):
        found.setdefault(item["incoming"], set()).add(item["skill"])
    return found


def collisions(root):
    packages = load_state(root).get("packages", {})
    oldest = datetime.min.replace(tzinfo=timezone.utc)

    def stamp(slug):
        record = packages.get(slug)
        return parse_time(record.get("last_check")) if isinstance(record, dict) else None

    owners = {}
    for slug, current in installed_packages(root).items():
        skills = current / "skills"
        for skill_dir in sorted(skills.iterdir()) if skills.is_dir() else []:
            name = skill_name(skill_dir) if skill_dir.is_dir() else None
            if name:
                owners.setdefault(name, []).append(slug)
    found = []
    for name, slugs in sorted(owners.items()):
        if len(slugs) < 2:
            continue
        incoming = max(slugs, key=lambda slug: (stamp(slug) or oldest, slug))
        found.append({"skill": name, "incoming": incoming, "loaded": [s for s in slugs if s != incoming]})
    return found


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
