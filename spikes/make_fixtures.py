"""Generate connector-fidelity fixtures and their sha256 manifest.

Usage: python spikes/make_fixtures.py   (writes spikes/drive-kit/)
Verify a copy: python spikes/make_fixtures.py --verify <dir>
"""
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).parent / "drive-kit"


def fixtures():
    tricky_py = (
        "# -*- coding: utf-8 -*-\n"
        "def parse(rows):\n"
        "\t# tab-indented on purpose\n"
        "\treturn [r.strip() for r in rows]   \n"  # trailing spaces
        "\n"
        "GREETING = \"שלום — ‘quotes’ “double” …\"\n"
        "EMOJI = \"✓ ✗ →\"\n"
        "RAW = r'\\d+\\s*\\\\'\n"
        "EMPTY_LINES_BELOW = True\n"
        "\n\n\n"
    )
    tricky_md = (
        "# כותרת בעברית\n\n"
        "| col | value |\n|---|---|\n| a | 1 |\n\n"
        "```python\nprint('hi')  \n```\n"
        "Line with two trailing spaces for a markdown break  \n"
        "No newline at end of file"
    )
    tricky_json = json.dumps(
        {"name": "fixture", "hebrew": "טבלה", "nested": {"list": [1, 2.50, None, True]}},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    crlf_txt = "line one\r\nline two\r\nlast line\r\n"
    lines = [
        f"def func_{i}(x):\n    \"\"\"Docstring {i} with ‘unicode’.\"\"\"\n    return x * {i} + {i % 7}\n\n"
        for i in range(600)
    ]
    large_py = "".join(lines)
    return {
        "tricky.py": tricky_py,
        "tricky.md": tricky_md,
        "tricky.json": tricky_json,
        "crlf.txt": crlf_txt,
        "large.py": large_py,
    }


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, text in fixtures().items():
        path = OUT / name
        path.write_bytes(text.encode("utf-8"))
        manifest.append({"path": name, "sha256": sha256(path), "bytes": path.stat().st_size})
    (OUT / "manifest.json").write_text(json.dumps({"files": manifest}, indent=2) + "\n")
    for entry in manifest:
        print(f"{entry['bytes']:>7}  {entry['sha256'][:16]}  {entry['path']}")


def verify(directory):
    manifest = json.loads((OUT / "manifest.json").read_text())
    ok = True
    for entry in manifest["files"]:
        path = Path(directory) / entry["path"]
        if not path.exists():
            print(f"MISSING   {entry['path']}")
            ok = False
            continue
        match = sha256(path) == entry["sha256"]
        ok &= match
        print(f"{'OK' if match else 'MISMATCH':<9} {entry['path']} ({path.stat().st_size} vs {entry['bytes']} bytes)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        verify(sys.argv[2])
    else:
        write()
