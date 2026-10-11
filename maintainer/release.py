#!/usr/bin/env python3
"""Build the framework zip, or one content-package zip, without uploading.

Writes <out>/<slug>/<slug>-<version>.zip, manifest.json, and current.json.
The framework zip is the framework/ directory of this repo. In a content zip every
skills/<skill>/scripts/*.py carries the sync gate from gate.py.

Usage:
  release.py --dry-run [--out DIR] [--min-version VER]
  release.py --dry-run --package DIR [--out DIR] [--min-version VER]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "framework" / "tools"))
import check  # noqa: E402
import gate  # noqa: E402
from common import (  # noqa: E402
    HUB_SLUG,
    PADDING_NAME,
    RELEASE_MIN_BYTES,
    RESERVED_SKILLS,
    SCIENCE_MAX_BYTES,
    tree_files,
    write_zip,
)


def main(argv):
    parser = argparse.ArgumentParser(description="Dry-run a framework or content release.")
    parser.add_argument("--dry-run", action="store_true", help="Write the zip locally. Required.")
    parser.add_argument("--package", type=Path, help="Content package directory. Omit for the framework zip.")
    parser.add_argument("--out", type=Path, default=Path("dist"), help="Output directory. Default: ./dist")
    parser.add_argument("--min-version", help="Version floor written into current.json.")
    args = parser.parse_args(argv)
    if not args.dry_run:
        print("upload is not implemented; pass --dry-run", file=sys.stderr)
        return 1
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
    print(f"dry-run package={slug} version={version} sha256={digest} bytes={current['zip_bytes']} zip={zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
