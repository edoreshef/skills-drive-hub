#!/usr/bin/env python3
"""Install one content package from a connector download.

The download is either a saved download_file_content tool result (JSON, content
as base64) or a file of inline base64 the agent wrote out. sha256 is checked
before anything is written. A refusal leaves every installed package as it was.

Usage:
  install.py --package SLUG --sha256 HEX (--from-tool-result FILE | --base64-file FILE)
             [--bytes N] [--version VER] [--current-file-id ID] [--root DIR]
"""

import argparse
import base64
import hashlib
import hmac
import io
import json
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from common import (
    DEFAULT_ROOT,
    PADDING_NAME,
    SLUG_RE,
    is_conflict_copy,
    is_credential,
    load_state,
    save_state,
    utc_now,
)


class InstallError(Exception):
    pass


def main(argv):
    parser = argparse.ArgumentParser(description="Install one package from a downloaded zip.")
    parser.add_argument("--package", required=True, help="Package slug. Selects packages/<slug>/.")
    parser.add_argument("--sha256", required=True, help="Expected sha256 of the zip bytes.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-tool-result", type=Path, help="Saved download_file_content tool result.")
    source.add_argument("--base64-file", type=Path, help="File containing the zip as base64.")
    parser.add_argument("--bytes", type=int, help="Expected zip size.")
    parser.add_argument("--version", help="Expected package.json version, from current.json.")
    parser.add_argument("--current-file-id", help="Drive file ID of this package's current.json.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Install root. Default: ~/.skills-hub")
    args = parser.parse_args(argv)
    root = args.root.expanduser()
    try:
        if args.from_tool_result:
            data = load_tool_result(args.from_tool_result)
        else:
            data = decode_b64(args.base64_file.read_text(encoding="utf-8"), is_zip)
            if data is None:
                raise InstallError("base64 file did not decode to a zip")
        version = install(root, args.package, data, args.sha256, args.bytes, args.version, args.current_file_id)
    except InstallError as exc:
        report_refusal(root, args.package, exc)
        return 1
    print(report_installed(root, args.package, version, data))
    return 0


def install(root, slug, data, expected_sha, expected_bytes=None, expected_version=None, current_file_id=None):
    """Verify, unpack, and swap one package. Returns the installed version."""
    if not SLUG_RE.fullmatch(slug):
        raise InstallError(f"invalid package slug {slug!r}")
    expected_sha = expected_sha.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise InstallError("sha256 must be 64 hex characters")
    actual = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(actual, expected_sha):
        raise InstallError(f"sha256 mismatch (expected {expected_sha}, got {actual})")
    if expected_bytes is not None and len(data) != expected_bytes:
        raise InstallError(f"size mismatch (expected {expected_bytes} bytes, got {len(data)})")
    try:
        state = load_state(root, strict=True)
    except ValueError as exc:
        raise InstallError(str(exc)) from None
    extract_root, version = extract_zip(data, slug, expected_version)
    try:
        activate(root, slug, extract_root)
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)
    packages = state.setdefault("packages", {})
    previous = packages.get(slug) or {}
    packages[slug] = {
        "version": version,
        "sha256": actual,
        "bytes": len(data),
        "current_file_id": current_file_id or previous.get("current_file_id"),
        "last_check": utc_now(),
    }
    save_state(root, state)
    return version


def report_installed(root, slug, version, data):
    current = root / "packages" / slug / "current"
    return (
        f"installed package={slug} version={version} "
        f"sha256={hashlib.sha256(data).hexdigest()} bytes={len(data)} current={current}"
    )


def report_refusal(root, slug, exc):
    print(f"refusing install of {slug}: {exc}", file=sys.stderr)
    current = root / "packages" / slug / "current"
    if SLUG_RE.fullmatch(slug) and current.is_dir():
        print(f"left {current} unchanged", file=sys.stderr)
    else:
        print(f"nothing written under {root}", file=sys.stderr)


def is_zip(data):
    return data.startswith(b"PK")


def read_download(path, accept, what):
    """(bytes, Drive file ID or None) from the raw file, a saved download_file_content result, or inline base64."""
    raw = path.read_bytes()
    if accept(raw):
        return raw, None
    text = raw.decode("utf-8", errors="replace")
    data = decode_b64(text, accept)
    if data is not None:
        return data, None
    node = parse_tool_result(text)
    data, file_id = find_payload(node, accept) if node is not None else (None, None)
    if data is None:
        raise InstallError(f"{path} is not {what}, a saved download_file_content result, or base64 of one")
    return data, file_id


def load_tool_result(path):
    node = parse_tool_result(path.read_text(encoding="utf-8"))
    data, _ = find_payload(node, is_zip) if node is not None else (None, None)
    if data is None:
        raise InstallError("tool result has no base64 zip")
    return data


def parse_tool_result(text):
    """The JSON in a saved tool result, which may have text before or after it."""
    start, end = text.find("{"), text.rfind("}")
    for candidate in (text, text[start : end + 1] if 0 <= start < end else ""):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def find_payload(node, accept, depth=0):
    """(bytes, file ID) of the first base64 value that passes accept, preferring 'content' keys.

    Nested JSON strings are searched too. The file ID is the 'id' next to the matched value.
    """
    if depth > 8:
        return None, None
    if isinstance(node, str):
        data = decode_b64(node, accept)
        if data is None and node.strip()[:1] in "{[":
            try:
                return find_payload(json.loads(node), accept, depth + 1)
            except json.JSONDecodeError:
                pass
        return data, None
    if isinstance(node, dict):
        values = ([node["content"]] if "content" in node else []) + [v for k, v in node.items() if k != "content"]
    elif isinstance(node, list):
        values = node
    else:
        return None, None
    for value in values:
        if isinstance(node, dict) and isinstance(value, str):
            data = decode_b64(value, accept)
            if data is not None:
                file_id = node.get("id")
                return data, file_id if isinstance(file_id, str) else None
            if value.strip()[:1] not in ("{", "["):
                continue
        data, file_id = find_payload(value, accept, depth + 1)
        if data is not None:
            return data, file_id
    return None, None


def decode_b64(text, accept):
    compact = "".join(text.split())
    if len(compact) < 8 or len(compact) % 4 == 1:
        return None
    try:
        data = base64.b64decode(compact, validate=True)
    except ValueError:
        return None
    return data if accept(data) else None


def extract_zip(data, slug, expected_version):
    """Unpack into a temp directory and validate package.json. Returns (directory, version)."""
    extract_root = Path(tempfile.mkdtemp(prefix="skills-hub-unpack-"))
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                refuse_member(info)
                if info.is_dir() or info.filename == PADDING_NAME:
                    continue
                target = extract_root / PurePosixPath(info.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
        meta_path = extract_root / "package.json"
        if not meta_path.is_file():
            raise InstallError("zip has no package.json")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise InstallError("package.json is not JSON") from None
        if meta.get("package") != slug:
            raise InstallError(f"package.json says {meta.get('package')!r}, not {slug!r}")
        version = meta.get("version")
        if not isinstance(version, str) or not version:
            raise InstallError("package.json has no version")
        if expected_version is not None and version != expected_version:
            raise InstallError(f"version {version} does not match expected {expected_version}")
        if not isinstance(meta.get("maintainers"), list) or not meta["maintainers"]:
            raise InstallError("package.json has no maintainers")
    except zipfile.BadZipFile:
        shutil.rmtree(extract_root, ignore_errors=True)
        raise InstallError("download is not a zip") from None
    except InstallError:
        shutil.rmtree(extract_root, ignore_errors=True)
        raise
    return extract_root, version


def refuse_member(info):
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if not name or name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in path.parts:
        raise InstallError(f"zip path escapes the package: {info.filename}")
    if stat.S_ISLNK(info.external_attr >> 16):
        raise InstallError(f"zip contains a symlink: {info.filename}")
    if info.is_dir():
        return
    if is_credential(path.name):
        raise InstallError(f"zip contains a credential-like file: {info.filename}")
    if is_conflict_copy(path.name):
        raise InstallError(f"zip contains a conflict copy: {info.filename}")
    if path.as_posix() == "tools/install.py":
        raise InstallError("content zip contains tools/install.py")


def activate(root, slug, extract_root):
    """staging <- unpacked tree, then current -> previous and staging -> current."""
    package_dir = root / "packages" / slug
    staging, current, previous = package_dir / "staging", package_dir / "current", package_dir / "previous"
    package_dir.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    shutil.move(str(extract_root), str(staging))
    if previous.exists():
        shutil.rmtree(previous)
    try:
        if current.exists():
            current.rename(previous)
        staging.rename(current)
    except OSError:
        if previous.exists() and not current.exists():
            previous.rename(current)
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
