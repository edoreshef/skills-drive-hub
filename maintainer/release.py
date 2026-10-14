#!/usr/bin/env python3
"""Build the framework zip, or one content-package zip; with --upload, release it to Drive.

Writes <out>/<slug>/<slug>-<version>.zip, manifest.json, and current.json.
The framework zip is the framework/ directory of this repo. In a content zip every
skills/<skill>/scripts/*.py carries the sync gate from gate.py.

--upload (design.md "Release"): the zip goes into the package's releases/ folder as a new
immutable file (a second upload of the same version is refused), Drive's sha256Checksum is compared with the local
hash (or the file is downloaded back and hashed), and only then is current.json rewritten in place by a media
update, so its file ID never changes and a half-uploaded release is never pointed at. A content release also
writes its current.json ID into index.json on the Skills Hub drive; a framework release refreshes the START HERE
docs. The drives come from setup_drive.py (registry ~/.config/skills-hub/drives.json).

Usage:
  release.py --dry-run [--out DIR] [--min-version VER]
  release.py --dry-run --package DIR [--out DIR] [--min-version VER]
  release.py --upload [--package DIR] [--out DIR] [--min-version VER] [--account EMAIL] [--maintainer EMAIL]

The framework tree keeps the placeholder maintainer (common.MAINTAINER_PLACEHOLDER) so the public repo names nobody.
A framework release writes the deployment's maintainer into the zip instead: --maintainer, else the account in the
Drive registry. --dry-run without --maintainer leaves the placeholder.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "framework" / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402
import gate  # noqa: E402
from common import (  # noqa: E402
    HUB_SLUG,
    MAINTAINER_PLACEHOLDER,
    PADDING_NAME,
    RELEASE_MIN_BYTES,
    RESERVED_SKILLS,
    SCIENCE_MAX_BYTES,
    tree_files,
    write_zip,
)


def main(argv):
    parser = argparse.ArgumentParser(description="Build (and with --upload, publish) a framework or content release.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Write the zip locally only.")
    mode.add_argument("--upload", action="store_true", help="Write the zip locally, then release it to Drive.")
    parser.add_argument("--package", type=Path, help="Content package directory. Omit for the framework zip.")
    parser.add_argument("--out", type=Path, default=Path("dist"), help="Output directory. Default: ./dist")
    parser.add_argument("--min-version", help="Version floor written into current.json.")
    parser.add_argument("--account", help="Google account for gcloud (default: the registry's).")
    parser.add_argument("--maintainer", help="Framework releases: the deployment's maintainer, written into the zip "
                                             f"in place of {MAINTAINER_PLACEHOLDER} (default: the registry's account).")
    args = parser.parse_args(argv)
    framework = args.package is None
    package_dir = REPO / "framework" if framework else args.package

    meta, findings = check.scan(package_dir)
    for finding in findings:
        print(finding.line(), file=sys.stderr)
    if any(finding.level == "blocking" for finding in findings):
        print("refusing release", file=sys.stderr)
        return 1
    slug, version = meta["package"], meta["version"]
    files = [(rel, path.read_bytes()) for path, rel in tree_files(package_dir) if rel != "manifest.json"]
    if framework:
        foreign = sorted({rel.split("/")[1] for rel, _ in files if rel.startswith("skills/")} - RESERVED_SKILLS)
        if slug != HUB_SLUG or foreign:
            print(f"refusing release: framework tree has package {slug!r}, extra skills {foreign}", file=sys.stderr)
            return 1
        maintainer = args.maintainer or (deployment_account(args.account) if args.upload else None)
        if args.upload and not maintainer:
            print("refusing release: no maintainer for the framework zip (pass --maintainer, or set up the Drive "
                  "registry with setup_drive.py --account)", file=sys.stderr)
            return 1
        if maintainer:
            files = substitute_maintainer(files, maintainer)
    elif slug == HUB_SLUG:
        print(f"refusing release: {HUB_SLUG} is the framework's slug, not a content package's", file=sys.stderr)
        return 1
    elif any(rel == "tools/install.py" for rel, _ in files):
        print("refusing release: content zip contains tools/install.py", file=sys.stderr)
        return 1
    if any(rel == PADDING_NAME for rel, _ in files):
        print(f"refusing release: {PADDING_NAME} is reserved for release padding", file=sys.stderr)
        return 1
    if not framework:
        gated = []
        for rel, data in files:
            try:
                gated.append((rel, gate.add_gate(data, slug) if gate.is_gated(rel) else data))
            except gate.GateError as exc:
                print(f"refusing release: {rel}: {exc}", file=sys.stderr)
                return 1
        files = gated
        oversized = [rel for rel, data in files if gate.is_gated(rel) and len(data) > SCIENCE_MAX_BYTES]
        if oversized:
            print(f"refusing release: over 64 KiB with the sync gate: {', '.join(oversized)}", file=sys.stderr)
            return 1

    manifest = {
        "files": [{"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for rel, data in files]
    }
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    dest = args.out / slug
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / f"{slug}-{version}.zip"
    write_zip(zip_path, files + [("manifest.json", manifest_text.encode("utf-8"))], RELEASE_MIN_BYTES)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    current = {
        "package": slug,
        "version": version,
        "min_version": args.min_version or version,
        "zip_file_id": None,
        "zip_sha256": digest,
        "zip_bytes": zip_path.stat().st_size,
    }
    (dest / "manifest.json").write_text(manifest_text, encoding="utf-8")
    (dest / "current.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"{'dry-run' if args.dry_run else 'built'} package={slug} version={version} sha256={digest} "
          f"bytes={current['zip_bytes']} zip={zip_path}")
    if args.dry_run:
        return 0
    try:
        return upload(slug, version, zip_path, current, dest, framework, args.account)
    except Exception as exc:  # noqa: BLE001 - one line for the maintainer, and a non-zero exit
        print(f"refusing release: {exc}", file=sys.stderr)
        return 1


def deployment_account(account=None):
    """The registry's Google account (the maintainer who set up the drives), or None."""
    from drive import load_registry
    return account or load_registry().get("account")


def substitute_maintainer(files, maintainer):
    """The framework tree carries the placeholder maintainer so the public repo names nobody; the released zip
    names the deployment's. Replaced in package.json `maintainers` and in each framework skill's `owner:` line."""
    out = []
    for rel, data in files:
        if rel == "package.json" or (rel.startswith("skills/") and rel.endswith("/SKILL.md")):
            data = data.decode("utf-8").replace(MAINTAINER_PLACEHOLDER, maintainer).encode("utf-8")
        out.append((rel, data))
    return out


def upload(slug, version, zip_path, current, dest, framework, account=None, drive=None, registry=None):
    """Release the built zip to Drive (see the module docstring). `drive` and `registry` are injectable for tests."""
    import setup_drive
    from drive import Drive, load_registry, save_registry

    registry = registry if registry is not None else load_registry()
    drive = drive or Drive(account or registry.get("account"))
    entry = registry.get("hub", {}) if framework else registry.get("packages", {}).get(slug)
    if not entry or not entry.get("releases"):
        raise RuntimeError(f"no Drive set up for {slug}: run setup_drive.py {'hub' if framework else '--package ' + slug}")

    # 1. the zip: a new immutable file under releases/
    if drive.children(entry["releases"], zip_path.name):
        raise RuntimeError(f"{zip_path.name} is already released; bump the version instead of re-releasing")
    data = zip_path.read_bytes()
    uploaded = drive.upload(zip_path.name, entry["releases"], data, "application/zip")
    remote = uploaded.get("sha256Checksum")
    if remote is None:                                  # Drive didn't compute one yet: read it back
        remote = hashlib.sha256(drive.download(uploaded["id"])).hexdigest()
    if remote != current["zip_sha256"] or int(uploaded.get("size") or len(data)) != current["zip_bytes"]:
        raise RuntimeError(f"Drive holds different bytes for {zip_path.name} (sha256 {remote}); current.json not updated")

    # 2. current.json, rewritten in place last
    current = {**current, "zip_file_id": uploaded["id"]}
    pointer = setup_drive._json_file(drive, entry["published_root"], "current.json", current, entry.get("current_json"))
    entry["current_json"] = pointer["id"]
    (dest / "current.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

    # 3. the pointers people read: index.json for a package, START HERE for both
    if not framework:
        setup_drive.update_index(drive, registry)
    setup_drive.refresh_start_here(drive, registry, None if framework else slug)
    save_registry(registry)
    print(f"released package={slug} version={version} zip_file_id={uploaded['id']} current_file_id={pointer['id']}")
    print("now tag the repo:  git tag v" + version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
