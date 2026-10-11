#!/usr/bin/env python3
"""Update one installed package from a current.json and its zip.

Same version: refresh that package's last_check, clear pending_version, and leave
every tree as it was. Another version is first recorded as pending_version, which
blocks the package's gated scripts until install.install() replaces the record.
A refusal leaves all package trees as they were. This does not download; the
caller passes files the connector saved.
Each file may be the raw file, a saved download_file_content result, or the
inline base64 the agent wrote out.

Usage:
  sync.py --root DIR --from-release DIR
  sync.py --root DIR --current FILE --zip FILE
"""

import argparse
import json
import sys
from pathlib import Path

import install
from common import DEFAULT_ROOT, installed_version, load_state, save_state, utc_now


def main(argv):
    parser = argparse.ArgumentParser(description="Install a package when its current.json version moved.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Install root. Default: ~/.skills-hub")
    parser.add_argument("--from-release", type=Path, help="Dry-run directory with current.json and the zip.")
    parser.add_argument("--current", type=Path, help="Downloaded current.json, when not using --from-release.")
    parser.add_argument("--zip", type=Path, help="Downloaded zip named by current.json, when not using --from-release.")
    parser.add_argument("--package", help="Package slug. Default: the slug in current.json.")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    try:
        current_path, zip_path = locate(args)
        pointer_bytes, current_file_id = install.read_download(current_path, is_pointer, "a current.json")
        pointer = json.loads(pointer_bytes)
    except (OSError, json.JSONDecodeError, KeyError, install.InstallError) as exc:
        print(f"refusing sync: {exc}", file=sys.stderr)
        return 1
    slug = args.package or pointer.get("package")
    if not slug:
        print("refusing sync: current.json has no package", file=sys.stderr)
        return 1
    version = pointer.get("version")
    floor = pointer.get("min_version") or version
    installed = installed_version(root, slug)

    if installed == version:
        if version_lt(installed, floor):
            print(f"refusing sync of {slug}: installed {installed} is below min_version {floor}", file=sys.stderr)
            print("sync required before using content skills", file=sys.stderr)
            return 1
        touch_last_check(root, slug)
        print(f"up to date package={slug} version={version}")
        return 0

    mark_pending(root, slug, version)
    if zip_path is None or not zip_path.is_file():
        if version_lt(installed or "0", floor):
            print(f"sync required before using content skills of {slug}", file=sys.stderr)
        print(f"refusing sync of {slug}: zip required to move from {installed or 'nothing'} to {version}", file=sys.stderr)
        return 1
    try:
        data, _ = install.read_download(zip_path, install.is_zip, "a zip")
        installed = install.install(root, slug, data, pointer["zip_sha256"], pointer.get("zip_bytes"), version,
                                    current_file_id)
    except install.InstallError as exc:
        install.report_refusal(root, slug, exc)
        return 1
    print(install.report_installed(root, slug, installed, data))
    return 0


def locate(args):
    if args.from_release:
        current_path = args.from_release / "current.json"
        pointer = json.loads(current_path.read_text(encoding="utf-8"))
        slug = args.package or pointer["package"]
        return current_path, args.from_release / f"{slug}-{pointer['version']}.zip"
    if args.current is None:
        raise OSError("pass --from-release or --current")
    return args.current, args.zip


def is_pointer(data):
    try:
        node = json.loads(data)
    except ValueError:
        return False
    return isinstance(node, dict) and "version" in node and "zip_sha256" in node


def touch_last_check(root, slug):
    state = load_state(root)
    record = state["packages"][slug]
    record["last_check"] = utc_now()
    record.pop("pending_version", None)
    save_state(root, state)


def mark_pending(root, slug, version):
    state = load_state(root)
    record = state.get("packages", {}).get(slug)
    if isinstance(record, dict) and record.get("pending_version") != version:
        record["pending_version"] = version
        save_state(root, state)


def version_lt(left, right):
    left_key, right_key = version_key(left), version_key(right)
    width = max(len(left_key), len(right_key))
    return left_key + (0,) * (width - len(left_key)) < right_key + (0,) * (width - len(right_key))


def version_key(value):
    """Leading digits of each dot-separated part: '1.2rc1' -> (1, 2)."""
    parts = []
    for piece in str(value).split("."):
        digits = ""
        for char in piece:
            if not char.isdigit():
                break
            digits += char
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
