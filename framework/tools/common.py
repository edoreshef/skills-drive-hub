"""Shared rules and helpers for the framework tools."""

import hashlib
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# The install root: ~/.skills-hub, or SKILLS_HUB_ROOT where ~ is not a place that persists (Claude Science's sandbox
# gives each cell a fresh home; its workspace directory persists, so START HERE sets SKILLS_HUB_ROOT inside it).
DEFAULT_ROOT = Path(os.environ.get("SKILLS_HUB_ROOT") or Path.home() / ".skills-hub").expanduser()
HUB_SLUG = "skills-hub"
# The framework tree names no real person: package.json and the framework skills carry this address, and
# release.py writes the deployment's maintainer into the zip in its place.
MAINTAINER_PLACEHOLDER = "r&d@example.com"

SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
CONFLICT_COPY_RE = re.compile(r" \(\d+\)(\.[^.]*)?$")
CREDENTIAL_NAMES = {
    ".env",
    ".netrc",
    "credentials.json",
    "id_dsa",
    "id_rsa",
    "secrets.json",
    "token.json",
}
RESERVED_SKILLS = {"sync", "publish", "feedback"}
# Claude Code returns a tool result of up to 50,000 characters inline, and the model then has to
# retype it. A 64 KiB zip is about 87,000 characters of base64, so it is always saved to a file.
RELEASE_MIN_BYTES = 64 * 1024
PADDING_NAME = "padding.bin"
SCIENCE_MAX_FILES = 64
SCIENCE_MAX_BYTES = 64 * 1024
BINARY_SUFFIXES = (
    ".exe",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".wasm",
    ".webp",
    ".zip",
)
BARE_DEPENDENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXACT_DEPENDENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*==[A-Za-z0-9][A-Za-z0-9.*_+!]*$")
FRONTMATTER_KEYS = ("name", "description", "owner", "data_sources")


def is_credential(name):
    base = name.lower()
    if base in CREDENTIAL_NAMES or base.startswith(".env."):
        return True
    if base.startswith(("client_secret", "service-account", "service_account")):
        return True
    return base.endswith((".pem", ".p12", ".key"))


def is_conflict_copy(name):
    return CONFLICT_COPY_RE.search(name) is not None


def is_binary_name(name):
    return name.lower().endswith(BINARY_SUFFIXES)


def parse_frontmatter(text):
    """Return (fields, None) or (None, error). All FRONTMATTER_KEYS are required."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing frontmatter"
    data = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        if not line.strip():
            continue
        if ":" not in line:
            return None, "invalid frontmatter"
        key, value = (part.strip() for part in line.split(":", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if not key or not value:
            return None, "invalid frontmatter"
        data[key] = value
    if not closed:
        return None, "invalid frontmatter"
    missing = [key for key in FRONTMATTER_KEYS if key not in data]
    if missing:
        return None, "frontmatter missing " + ", ".join(missing)
    return data, None


def skill_name(skill_dir):
    """Frontmatter name of a skill directory, or None."""
    skill_file = Path(skill_dir) / "SKILL.md"
    if not skill_file.is_file():
        return None
    frontmatter, _ = parse_frontmatter(skill_file.read_text(encoding="utf-8", errors="replace"))
    return frontmatter["name"] if frontmatter else None


def load_state(root, strict=False):
    """state.json as a dict. strict raises ValueError on a damaged file instead of returning {}."""
    path = Path(root) / "state.json"
    if not path.is_file():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        if strict:
            raise ValueError("state.json is not JSON") from None
        return {}
    if not isinstance(state, dict) or not isinstance(state.get("packages", {}), dict):
        if strict:
            raise ValueError("state.json is not an object with a packages map")
        return {}
    return state


def save_state(root, state):
    write_json_atomic(Path(root) / "state.json", state)


def installed_version(root, slug):
    record = load_state(root).get("packages", {}).get(slug)
    return record.get("version") if isinstance(record, dict) else None


def write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value):
    if not isinstance(value, str):
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def author_token(author):
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", author.split("@", 1)[0])
    return token or "author"


def unique_path(path):
    if not path.exists():
        return path
    for number in range(2, 100):
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"too many files named {path.name}")


def write_zip(zip_path, entries, min_bytes=0):
    """Write (relative_path, bytes) pairs with fixed timestamps and modes, so equal input gives equal bytes.

    A zip under min_bytes gets a stored PADDING_NAME of hash-derived bytes that brings it up to size.
    """
    write_entries(zip_path, [(relative, data, zipfile.ZIP_DEFLATED) for relative, data in entries])
    short = min_bytes - zip_path.stat().st_size
    if short > 0:
        padding = hashlib.shake_256(zip_path.read_bytes()).digest(short)
        write_entries(zip_path, [(relative, data, zipfile.ZIP_DEFLATED) for relative, data in entries]
                      + [(PADDING_NAME, padding, zipfile.ZIP_STORED)])


def write_entries(zip_path, entries):
    with zipfile.ZipFile(zip_path, "w") as archive:
        for relative, data, compression in entries:
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = compression
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def write_marketplace(root):
    """<root>/.claude-plugin/marketplace.json: the local directory marketplace Claude Code registers once
    (`claude plugin marketplace add <root>`). One plugin per installed tree: framework/current and every
    packages/<slug>/current that has a plugin.json. Rewritten after every install, so swapping `current` is the
    update and a new package appears as a new plugin."""
    root = Path(root)
    plugins = []
    trees = [root / "framework" / "current"]
    packages = root / "packages"
    if packages.is_dir():
        trees += sorted(p / "current" for p in packages.iterdir() if (p / "current").is_dir())
    for tree in trees:
        manifest = tree / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            continue
        try:
            meta = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        plugins.append({"name": meta.get("name") or tree.parent.name,
                        "source": "./" + tree.relative_to(root).as_posix(),
                        "description": meta.get("description", ""),
                        "version": meta.get("version", "")})
    marketplace = {"name": "skills-hub", "owner": {"name": "Skills Hub"},
                   "description": "Skill packages shared through Google Drive, installed and kept current by Skills Hub.",
                   "plugins": plugins}
    target = root / ".claude-plugin" / "marketplace.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")
    return target


def tree_files(directory):
    """Regular files under directory as (path, relative), skipping symlinks, __pycache__ and .git (a package
    directory is usually a git checkout; the repository itself never ships)."""
    directory = Path(directory)
    return [
        (path, path.relative_to(directory).as_posix())
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.is_symlink() and not SKIPPED_PARTS & set(path.parts)
    ]


SKIPPED_PARTS = {"__pycache__", ".git"}
