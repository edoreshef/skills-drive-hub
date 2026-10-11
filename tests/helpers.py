"""Shared paths and helpers. Tests run each tool as a subprocess, the way an agent does."""

import base64
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "framework" / "tools"
MAINTAINER = ROOT / "maintainer"
FIXTURES = ROOT / "fixtures" / "packages"


def tool(name):
    return TOOLS / f"{name}.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(directory):
    """relative path -> sha256 for every regular file under directory."""
    if not directory.exists():
        return {}
    return {
        path.relative_to(directory).as_posix(): sha256(path.read_bytes())
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def zip_tree(src):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(src).as_posix())
    return buf.getvalue()


def zip_names(path):
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def copy_fixture(source, dest, slug, maintainers=None):
    """Copy a fixture package under a new slug."""
    shutil.copytree(source, dest)
    meta = read_json(dest / "package.json")
    meta["package"] = slug
    if maintainers:
        meta["maintainers"] = maintainers
    write_json(dest / "package.json", meta)
    plugin = dest / ".claude-plugin" / "plugin.json"
    if plugin.is_file():
        write_json(plugin, {**read_json(plugin), "name": slug})
    return dest


class ToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="skills-hub-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write_base64(self, name, data):
        """Inline base64 the agent wrote out, wrapped at 76 columns."""
        path = self.tmp / name
        encoded = base64.b64encode(data).decode("ascii")
        path.write_text("\n".join(encoded[i : i + 76] for i in range(0, len(encoded), 76)) + "\n", encoding="utf-8")
        return path

    def write_tool_result(self, name, data, file_id="file-id", nested=False):
        """A saved download_file_content result. nested: the JSON is a string inside a text block."""
        path = self.tmp / name
        payload = json.dumps({"content": base64.b64encode(data).decode("ascii"), "id": file_id,
                              "mimeType": "application/octet-stream", "title": name})
        if nested:
            payload = json.dumps([{"type": "text", "text": payload}])
        path.write_text("saved download_file_content result\n" + payload, encoding="utf-8")
        return path

    def release(self, out, package=None, min_version=None):
        args = ["--dry-run", "--out", out]
        if package is not None:
            args += ["--package", package]
        if min_version:
            args += ["--min-version", min_version]
        result = run(MAINTAINER / "release.py", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def install_release(self, root, release_dir):
        """Install a dry-run release the way an agent would after an inline download."""
        current = read_json(release_dir / "current.json")
        slug = current["package"]
        encoded = self.tmp / f"{slug}.b64"
        encoded.write_bytes(base64.b64encode((release_dir / f"{slug}-{current['version']}.zip").read_bytes()))
        result = run(
            tool("install"),
            "--package", slug,
            "--sha256", current["zip_sha256"],
            "--bytes", current["zip_bytes"],
            "--base64-file", encoded,
            "--root", root,
            "--version", current["version"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
