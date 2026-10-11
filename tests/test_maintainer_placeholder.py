"""The framework tree names no real person: every address in framework/ is the placeholder, and a framework
release substitutes the deployment's maintainer into the zip only."""
import io
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import MAINTAINER, ROOT, run

EMAIL = re.compile(r"[A-Za-z0-9._%+&-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PLACEHOLDER = "r&d@example.com"


class MaintainerPlaceholderTest(unittest.TestCase):
    def test_the_framework_tree_carries_only_the_placeholder(self):
        found = set()
        for path in (ROOT / "framework").rglob("*"):
            if path.is_file() and path.suffix in (".md", ".json", ".py", ".yaml", ".yml", ".txt"):
                found |= set(EMAIL.findall(path.read_text(encoding="utf-8", errors="replace")))
        self.assertEqual(found - {PLACEHOLDER}, set(), "a real address is in framework/: keep it for release.py")
        self.assertIn(PLACEHOLDER, json.loads((ROOT / "framework" / "package.json").read_text())["maintainers"])

    def _zip_texts(self, out):
        zip_path = next((out / "skills-hub").glob("*.zip"))
        with zipfile.ZipFile(zip_path) as archive:
            return {n: archive.read(n).decode("utf-8", "replace") for n in archive.namelist()
                    if n == "package.json" or n.endswith("SKILL.md")}

    def test_release_substitutes_the_maintainer_into_the_zip_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            result = run(MAINTAINER / "release.py", "--dry-run", "--out", out, "--maintainer", "lead@acme.test")
            self.assertEqual(result.returncode, 0, result.stderr)
            texts = self._zip_texts(out)
            self.assertEqual(json.loads(texts["package.json"])["maintainers"], ["lead@acme.test"])
            skills = [t for n, t in texts.items() if n.startswith("skills/") and n.endswith("SKILL.md")]
            self.assertEqual(len(skills), 3)
            self.assertIn("owner: __OWNER__", texts["templates/skill/SKILL.md"], "the template is left alone")
            for text in skills:
                self.assertIn("owner: lead@acme.test", text)
                self.assertNotIn(PLACEHOLDER, text)
        # the tree itself is untouched
        self.test_the_framework_tree_carries_only_the_placeholder()

    def test_dry_run_without_a_maintainer_keeps_the_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            self.assertEqual(run(MAINTAINER / "release.py", "--dry-run", "--out", out).returncode, 0)
            self.assertEqual(json.loads(self._zip_texts(out)["package.json"])["maintainers"], [PLACEHOLDER])


if __name__ == "__main__":
    unittest.main()
