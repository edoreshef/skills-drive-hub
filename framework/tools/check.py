#!/usr/bin/env python3
"""Structure check for one package directory.

Blocking findings fail the run. Warnings are printed and do not.
Prose review is left to the maintainer; this tool does not judge it.

Usage:
  check.py --package DIR [--baseline DIR]
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))  # PYTHONSAFEPATH-proof: common.py lives next to this file
from common import (
    BARE_DEPENDENCY,
    EXACT_DEPENDENCY,
    HUB_SLUG,
    RESERVED_SKILLS,
    SCIENCE_MAX_BYTES,
    SCIENCE_MAX_FILES,
    SKIPPED_PARTS,
    SLUG_RE,
    is_binary_name,
    is_conflict_copy,
    is_credential,
    parse_frontmatter,
    tree_files,
)

PEP723 = re.compile(r"^# /// script[ \t]*\n(.*?)^# ///[ \t]*$", re.M | re.S)
WORD = {
    "question": re.compile(r"\bquestion\b", re.I),
    "steps": re.compile(r"\bsteps\b", re.I),
    "answer": re.compile(r"\banswer\b", re.I),
}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
IMPORT_ROOTS = {"socket", "requests", "urllib", "subprocess"}


class Finding:
    def __init__(self, level, where, message):
        self.level = level
        self.where = where
        self.message = message

    def line(self):
        return f"{self.level}: {self.where}: {self.message}"


def main(argv):
    parser = argparse.ArgumentParser(description="Check one package directory.")
    parser.add_argument("--package", required=True, type=Path, help="Package directory.")
    parser.add_argument("--baseline", type=Path, help="Previous package tree, for the size warning.")
    args = parser.parse_args(argv)
    package_dir = args.package
    meta, findings = scan(package_dir, args.baseline)
    slug = meta.get("package") or package_dir.name
    maintainers = meta.get("maintainers") or []
    print(f"package: {slug}")
    print("maintainers: " + (", ".join(maintainers) if maintainers else "(none)"))
    for finding in findings:
        print(finding.line())
    blocking = sum(1 for finding in findings if finding.level == "blocking")
    warnings = sum(1 for finding in findings if finding.level == "warning")
    print(f"{blocking} blocking, {warnings} warnings")
    print("Prose review is not automated.")
    return 1 if blocking else 0


def scan(package_dir, baseline=None):
    findings = []
    meta = {}
    package_dir = Path(package_dir)
    if not package_dir.is_dir():
        return meta, [Finding("blocking", str(package_dir), "package directory is missing")]
    meta = read_package_json(package_dir, findings)
    slug = meta.get("package")
    walk_tree(package_dir, findings)
    skills_dir = package_dir / "skills"
    if not skills_dir.is_dir():
        findings.append(Finding("blocking", "skills", "no skills directory"))
    else:
        skill_dirs = [path for path in sorted(skills_dir.iterdir()) if path.is_dir() and not path.is_symlink()]
        if not skill_dirs:
            findings.append(Finding("blocking", "skills", "no skills"))
        names = {}
        for skill_dir in skill_dirs:
            name = scan_skill(skill_dir, slug, findings)
            if name:
                names.setdefault(name, []).append(skill_dir.name)
            if baseline:
                warn_size(skill_dir, baseline / "skills" / skill_dir.name, findings)
        for name, dirs in sorted(names.items()):
            if len(dirs) > 1:
                findings.append(Finding("blocking", "skills", f"skill name {name} collides"))
    findings.sort(key=lambda finding: (finding.level != "blocking", finding.where, finding.message))
    return meta, findings


def read_package_json(package_dir, findings):
    path = package_dir / "package.json"
    if not path.is_file():
        findings.append(Finding("blocking", "package.json", "missing"))
        return {}
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        findings.append(Finding("blocking", "package.json", "is not JSON"))
        return {}
    if not isinstance(meta, dict):
        findings.append(Finding("blocking", "package.json", "is not an object"))
        return {}
    slug = meta.get("package")
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        findings.append(Finding("blocking", "package.json", "package slug is missing or invalid"))
    maintainers = meta.get("maintainers")
    if not isinstance(maintainers, list) or not maintainers:
        findings.append(Finding("blocking", "package.json", "has no maintainers"))
    if not isinstance(meta.get("version"), str) or not meta.get("version"):
        findings.append(Finding("blocking", "package.json", "has no version"))
    return meta


def walk_tree(package_dir, findings):
    for path in sorted(package_dir.rglob("*")):
        if SKIPPED_PARTS & set(path.parts):
            continue
        relative = path.relative_to(package_dir).as_posix()
        if path.is_symlink():
            findings.append(Finding("blocking", relative, "symlink"))
            continue
        name = path.name
        if is_credential(name):
            findings.append(Finding("blocking", relative, "credential-like file"))
        if is_conflict_copy(name):
            findings.append(Finding("blocking", relative, "conflict copy"))
        if path.is_file() and path.stat().st_mode & 0o111:
            findings.append(Finding("blocking", relative, "executable bit set"))
        if path.is_file() and is_binary_name(name):
            findings.append(Finding("blocking", relative, "binary"))


def scan_skill(skill_dir, package_slug, findings):
    where = skill_dir.relative_to(skill_dir.parents[1]).as_posix()
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        findings.append(Finding("blocking", where, "missing SKILL.md"))
        return None
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    frontmatter, error = parse_frontmatter(text)
    if error:
        findings.append(Finding("blocking", f"{where}/SKILL.md", error))
        return None
    name = frontmatter["name"]
    if not SLUG_RE.fullmatch(name):
        findings.append(Finding("blocking", f"{where}/SKILL.md", f"invalid skill name {name}"))
        return None
    if package_slug != HUB_SLUG and name in RESERVED_SKILLS:
        findings.append(Finding("blocking", f"{where}/SKILL.md", f"reserved skill name {name}"))
    if not has_example(skill_dir):
        findings.append(Finding("blocking", where, "no example"))
    if not has_changes(skill_dir):
        findings.append(Finding("blocking", where, "no CHANGES.md entry"))
    files = [path for path, _ in tree_files(skill_dir)]
    if len(files) > SCIENCE_MAX_FILES:
        findings.append(Finding("blocking", where, f"more than {SCIENCE_MAX_FILES} files"))
    for path in files:
        if path.stat().st_size > SCIENCE_MAX_BYTES:
            relative = path.relative_to(skill_dir.parents[1]).as_posix()
            findings.append(Finding("blocking", relative, "over 64 KiB"))
        if contains_null(path):
            relative = path.relative_to(skill_dir.parents[1]).as_posix()
            findings.append(Finding("blocking", relative, "binary"))
    scripts = [
        path
        for path in files
        if path.suffix == ".py" and path.relative_to(skill_dir).parts[:1] == ("scripts",)
    ]
    tests = [path for path in files if path.relative_to(skill_dir).parts[:1] == ("tests",) and path.suffix == ".py"]
    if scripts and not tests:
        findings.append(Finding("warning", where, "no tests/ for a script"))
    for script in scripts:
        scan_script(script, skill_dir, findings)
    for test in tests:
        run_test(test, skill_dir, findings)
    return name


def scan_script(script, skill_dir, findings):
    relative = script.relative_to(skill_dir.parents[1]).as_posix()
    text = script.read_text(encoding="utf-8", errors="replace")
    parsed = parse_pep723(text)
    if parsed is None or parsed == "invalid":
        findings.append(Finding("blocking", relative, "no parseable PEP 723 block"))
        dependencies = []
    else:
        dependencies = parsed
    for dependency in dependencies:
        if BARE_DEPENDENCY.fullmatch(dependency) or EXACT_DEPENDENCY.fullmatch(dependency):
            findings.append(Finding("warning", relative, f"third-party dependency {dependency}"))
        else:
            findings.append(Finding("blocking", relative, f"dependency range {dependency}"))
    try:
        tree = ast.parse(text)
    except SyntaxError:
        findings.append(Finding("blocking", relative, "Python syntax error"))
        return
    for warning in import_warnings(tree):
        findings.append(Finding("warning", relative, warning))


def run_test(test, skill_dir, findings):
    relative = test.relative_to(skill_dir.parents[1]).as_posix()
    try:
        result = subprocess.run(
            [sys.executable, str(test.resolve())],     # absolute: cwd is the skill, --package may be relative
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        findings.append(Finding("warning", relative, "tests failed"))
        return
    if result.returncode != 0:
        findings.append(Finding("warning", relative, "tests failed"))


def import_warnings(tree):
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in IMPORT_ROOTS:
                    found.append(f"imports {root}")
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module:
                root = node.module.split(".", 1)[0]
                if root in IMPORT_ROOTS:
                    found.append(f"imports {root}")
            self.generic_visit(node)

        def visit_Call(self, node):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"eval", "exec"}:
                found.append(f"calls {func.id}")
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "system"
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
            ):
                found.append("calls os.system")
            if isinstance(func, ast.Name) and func.id in {"open", "Path"} and node.args:
                target = constant_text(node.args[0])
                if target and path_is_outside(target):
                    found.append("writes outside the working directory")
            self.generic_visit(node)

    Visitor().visit(tree)
    return found


def constant_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def path_is_outside(target):
    return target.startswith("/") or target.startswith("~") or target.startswith("..")


def parse_pep723(text):
    match = PEP723.search(text)
    if not match:
        return None
    dependencies = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            return "invalid"
        content = stripped[1:].strip()
        if not content:
            continue
        if "=" not in content:
            return "invalid"
        key, value = content.split("=", 1)
        if key.strip() != "dependencies":
            continue
        parsed = parse_dependency_list(value.strip())
        if parsed is None:
            return "invalid"
        dependencies = parsed
    return dependencies


def parse_dependency_list(value):
    if not (value.startswith("[") and value.endswith("]")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return []
    parts = re.findall(r'"([^"]*)"|\'([^\']*)\'', inner)
    if not parts:
        return None
    return [left or right for left, right in parts]


def has_example(skill_dir):
    examples = skill_dir / "examples"
    if not examples.is_dir():
        return False
    for path in examples.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if all(pattern.search(text) for pattern in WORD.values()):
            return True
    return False


def has_changes(skill_dir):
    path = skill_dir / "CHANGES.md"
    if not path.is_file():
        return False
    return DATE.search(path.read_text(encoding="utf-8", errors="replace")) is not None


def contains_null(path):
    with path.open("rb") as handle:
        return b"\0" in handle.read(8192)


def warn_size(skill_dir, previous, findings):
    if not previous.is_dir():
        return
    old = sum(path.stat().st_size for path, _ in tree_files(previous))
    new = sum(path.stat().st_size for path, _ in tree_files(skill_dir))
    if old and new - old > max(4096, old // 2):
        where = skill_dir.relative_to(skill_dir.parents[1]).as_posix()
        findings.append(Finding("warning", where, "large size increase"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
