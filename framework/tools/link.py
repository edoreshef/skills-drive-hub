#!/usr/bin/env python3
"""Link installed packages into Cursor's skills directory.

One symlink per package, aimed at that package's current/. A skill name that
doctor blocks is left out of the incoming package's link. Markers in
links.json record the links this tool created; removal touches only those.

Windows uses a directory junction. That path is not tested here.

Usage:
  link.py --root DIR [--skills-dir DIR]
  link.py --root DIR --unlink SLUG [--skills-dir DIR]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # PYTHONSAFEPATH-proof: common.py lives next to this file
import doctor  # noqa: E402
from common import DEFAULT_ROOT, HUB_SLUG, skill_name, write_json_atomic


def main(argv):
    parser = argparse.ArgumentParser(description="Link installed packages into Cursor's skills directory.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Install root. Default: ~/.skills-hub")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".cursor" / "skills")
    parser.add_argument("--unlink", help="Remove the link for this package slug and stop.")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    skills_dir = args.skills_dir.expanduser()
    if args.unlink:
        return unlink(root, args.unlink)
    return refresh(root, skills_dir)


def refresh(root, skills_dir):
    skills_dir.mkdir(parents=True, exist_ok=True)
    markers = load_markers(root)
    installed = installed_current(root)
    blocked = doctor.blocked_skill_names(root)
    for slug in list(markers):
        if slug not in installed:
            if remove_owned(Path(markers[slug]["path"]), markers[slug]):
                remove_view(root, slug)
                print(f"removed {slug}")
            markers.pop(slug, None)
    for slug, current in sorted(installed.items()):
        outcome = place(root, skills_dir, slug, current, blocked.get(slug, set()), markers)
        print(outcome)
    save_markers(root, markers)
    return 0


def unlink(root, slug):
    markers = load_markers(root)
    record = markers.get(slug)
    if not record:
        print(f"no link recorded for {slug}")
        return 0
    link = Path(record["path"])
    if remove_owned(link, record):
        remove_view(root, slug)
        markers.pop(slug, None)
        save_markers(root, markers)
        print(f"removed {slug}")
        return 0
    print(f"left {link} in place")
    return 0


def place(root, skills_dir, slug, current, blocked_names, markers):
    link = skills_dir / slug
    record = markers.get(slug)
    if link.exists() or link.is_symlink():
        if not owned(link, record):
            return f"left {link} in place"
        link.unlink()
    if blocked_names:
        target = materialize_view(root, slug, current, blocked_names)
    else:
        remove_view(root, slug)
        target = current.resolve()
    make_dir_link(link, target)
    markers[slug] = {"path": str(link), "target": str(target)}
    if blocked_names:
        names = ", ".join(sorted(blocked_names))
        return f"linked {slug} without {names}"
    return f"linked {slug}"


def installed_current(root):
    found = {}
    framework = root / "framework" / "current"
    if (framework / "package.json").is_file():
        found[HUB_SLUG] = framework
    found.update(doctor.installed_packages(root))
    return found


def materialize_view(root, slug, current, blocked_names):
    view = root / "views" / slug
    if view.exists() or view.is_symlink():
        shutil.rmtree(view)
    view.mkdir(parents=True)
    for child in sorted(current.iterdir()):
        if child.name == "skills":
            skills = view / "skills"
            skills.mkdir()
            for skill_dir in sorted(path for path in child.iterdir() if path.is_dir()):
                if skill_name(skill_dir) in blocked_names:
                    continue
                make_dir_link(skills / skill_dir.name, skill_dir.resolve())
            continue
        dest = view / child.name
        if child.is_dir():
            make_dir_link(dest, child.resolve())
        else:
            dest.symlink_to(child.resolve())
    return view.resolve()


def make_dir_link(link, target):
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
        return
    link.symlink_to(target, target_is_directory=True)


def owned(link, record):
    if not record or not link.is_symlink():
        return False
    if Path(record["path"]) != link:
        return False
    try:
        return link.resolve() == Path(record["target"]).resolve()
    except OSError:
        return False


def remove_owned(link, record):
    if not owned(link, record):
        return False
    link.unlink()
    return True


def remove_view(root, slug):
    view = root / "views" / slug
    if view.exists() or view.is_symlink():
        shutil.rmtree(view)


def load_markers(root):
    path = root / "links.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    packages = data.get("packages") if isinstance(data, dict) else None
    return packages if isinstance(packages, dict) else {}


def save_markers(root, packages):
    write_json_atomic(root / "links.json", {"packages": packages})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
