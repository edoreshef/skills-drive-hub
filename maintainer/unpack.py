#!/usr/bin/env python3
"""A release zip as the package's source tree: the review baseline, or what a catch-up commit holds when a release
reached Drive without one.

Usage:
  unpack.py --package SLUG --out DIR                      the release current.json names on Drive
  unpack.py --zip FILE --out DIR                          a release zip on disk
  unpack.py --package SLUG --out DIR --submission NAME    the same, with an inbox/ submission laid over its skill

The zip is checked against its manifest.json; manifest.json, padding.bin and test caches are left out and the sync
gate is taken out of every script, so the tree compares with the package repo (a gate from an older Skills Hub can
leave a blank line behind). With --submission the skill directory is replaced
by the submission's files (submission.json included, which review.py reads) and the drive's last modifier of the
zip is printed for review.py --drive-modifier.
"""

import argparse
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "framework" / "tools"))
from common import PADDING_NAME, SKIPPED_PARTS  # noqa: E402
from gate import is_gated, strip_gate  # noqa: E402


def unpack_release(data, out):
    archive = zipfile.ZipFile(io.BytesIO(data))
    manifest = json.loads(archive.read("manifest.json"))
    listed = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    names = [n for n in archive.namelist() if not n.endswith("/") and n not in ("manifest.json", PADDING_NAME)]
    if sorted(names) != sorted(listed):
        raise SystemExit("error: the zip's files do not match its manifest.json")
    for name in names:
        body = archive.read(name)
        if hashlib.sha256(body).hexdigest() != listed[name]:
            raise SystemExit(f"error: {name} does not match its manifest.json hash")
        if SKIPPED_PARTS & set(name.split("/")):
            continue
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(strip_gate(body) if is_gated(name) else body)
    return json.loads((out / "package.json").read_text(encoding="utf-8"))


def overlay_submission(data, out):
    archive = zipfile.ZipFile(io.BytesIO(data))
    submission = json.loads(archive.read("submission.json"))
    skill_dir = out / "skills" / submission["skill"]
    shutil.rmtree(skill_dir, ignore_errors=True)
    for name in archive.namelist():
        if not name.endswith("/"):
            target = skill_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    return submission


def main(argv):
    parser = argparse.ArgumentParser(description="Unpack a release zip into the package's source tree.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--package", help="package slug: the release current.json names on Drive")
    source.add_argument("--zip", type=Path, help="a release zip on disk")
    parser.add_argument("--out", type=Path, required=True, help="directory to write; must not exist")
    parser.add_argument("--submission", help="file name of a submission in the package's inbox/ to lay over it")
    parser.add_argument("--account")
    args = parser.parse_args(argv)
    if args.out.exists():
        print(f"error: {args.out} exists", file=sys.stderr)
        return 1
    if args.submission and not args.package:
        print("error: --submission needs --package", file=sys.stderr)
        return 1
    drive = None
    if args.package:
        from drive import Drive, load_registry
        registry = load_registry()
        entry = registry.get("packages", {}).get(args.package)
        if not entry or not entry.get("current_json"):
            print(f"error: no release of {args.package} on Drive", file=sys.stderr)
            return 1
        drive = Drive(args.account or registry.get("account"))
        current = json.loads(drive.download(entry["current_json"]))
        data = drive.download(current["zip_file_id"])
        if hashlib.sha256(data).hexdigest() != current["zip_sha256"]:
            print("error: the release zip does not match current.json", file=sys.stderr)
            return 1
    else:
        data = args.zip.read_bytes()
    args.out.mkdir(parents=True)
    meta = unpack_release(data, args.out)
    print(f"unpacked {meta.get('package')} {meta.get('version')} into {args.out}")
    if args.submission:
        inbox = entry["submissions"]["inbox"]
        match = [f for f in drive.children(inbox) if f["name"] == args.submission]
        if len(match) != 1:
            print(f"error: {len(match)} files named {args.submission} in inbox/", file=sys.stderr)
            return 1
        submission = overlay_submission(drive.download(match[0]["id"]), args.out)
        modifier = drive.get(match[0]["id"], "lastModifyingUser(emailAddress)").get("lastModifyingUser", {})
        print(f"laid {args.submission} over skills/{submission['skill']}; "
              f"drive last modifier: {modifier.get('emailAddress', 'unknown')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
