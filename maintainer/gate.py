"""The sync gate that release.py adds to every content script.

A gated script runs only if its package's state.json record has a last_check within
MAX_AGE_HOURS and no pending_version. Under packages/<slug>/current/ it reads that root's
state.json and fails closed. Anywhere else it reads SKILLS_HUB_ROOT/state.json if that variable is
set (Claude Science: START HERE points it at the workspace, which persists; the published skill
directory does not) and fails closed; else ~/.skills-hub/state.json if one exists, failing closed;
and with neither it warns and runs.
"""

import ast
import re

MAX_AGE_HOURS = 24
BLOCKED_EXIT = 75
MARKER = "_skills_hub_gate"

TEMPLATE = '''\
# skills-hub sync gate, added at release. The package's source repo does not have it.
def _skills_hub_gate(slug=__SLUG__, max_age=__MAX_AGE__):
    import json
    import os
    import sys
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    def block(reason):
        print(f"blocked: package {slug}: {reason}. Run the sync skill, then run this script again.",
              file=sys.stderr)
        sys.exit(__EXIT__)

    roots = [p.parents[2] for p in Path(__file__).resolve().parents
             if p.name == "current" and p.parent.name == slug and p.parent.parent.name == "packages"]
    env_root = os.environ.get("SKILLS_HUB_ROOT")
    root = roots[0] if roots else Path(env_root).expanduser() if env_root else Path(os.path.expanduser("~")) / ".skills-hub"
    if not roots and not env_root and not (root / "state.json").exists():
        print(f"warning: package {slug}: no ~/.skills-hub on this host and SKILLS_HUB_ROOT is not set, so sync "
              f"status is not checked.", file=sys.stderr)
        return
    try:
        record = json.loads((root / "state.json").read_text(encoding="utf-8"))["packages"][slug]
        pending, checked = record.get("pending_version"), record["last_check"]
        when = datetime.fromisoformat(checked[:-1] + "+00:00" if checked.endswith("Z") else checked)
    except (OSError, ValueError, LookupError, TypeError, AttributeError):
        block(f"no readable sync record in {root / 'state.json'}")
    if pending:
        block(f"update {pending} is available")
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - when
    if age < timedelta(0):
        block(f"last sync check {checked} is in the future")
    if age > timedelta(hours=max_age):
        block(f"last sync check {checked} is over {max_age}h old")


_skills_hub_gate()
del _skills_hub_gate
'''

HEADER_LINE = re.compile(r"^\s*(#.*)?$")


class GateError(Exception):
    pass


def is_gated(relative):
    parts = relative.split("/")
    return len(parts) >= 4 and parts[0] == "skills" and parts[2] == "scripts" and relative.endswith(".py")


def gate_source(slug):
    return (TEMPLATE.replace("__SLUG__", repr(slug))
            .replace("__MAX_AGE__", str(MAX_AGE_HOURS))
            .replace("__EXIT__", str(BLOCKED_EXIT)))


def add_gate(data, slug):
    """Script bytes with the gate after the header comments, docstring, and __future__ imports."""
    try:
        text = data.decode("utf-8")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise GateError(f"cannot add the sync gate: {exc}") from None
    if MARKER in text:
        raise GateError(f"cannot add the sync gate: the script already uses the name {MARKER}")
    lines = text.splitlines(keepends=True)
    at = 0
    while at < len(lines) and HEADER_LINE.match(lines[at]):
        at += 1
    while at and not lines[at - 1].strip():
        at -= 1
    body = list(tree.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        at = max(at, body.pop(0).end_lineno)
    while body and isinstance(body[0], ast.ImportFrom) and body[0].module == "__future__":
        at = max(at, body.pop(0).end_lineno)
    head, tail = lines[:at], lines[at:]
    if head and not head[-1].endswith("\n"):
        head[-1] += "\n"
    gate = gate_source(slug)
    if head:
        gate = "\n" + gate
    if tail:
        gate += "\n"
    return ("".join(head) + gate + "".join(tail)).encode("utf-8")


GATE_BLOCK = re.compile(r"\n?(?:# skills-hub sync gate[^\n]*\n)?def _skills_hub_gate\(.*?^del _skills_hub_gate\n\n?",
                        re.S | re.M)


def strip_gate(data):
    """Script bytes with the sync gate taken out: the inverse of add_gate for this version's gate. A gate written by
    an older Skills Hub is also removed, but a blank line it added may stay."""
    text = data.decode("utf-8")
    stripped, count = GATE_BLOCK.subn("", text, count=1)
    return stripped.encode("utf-8") if count else data
