"""check, release, draft, publish, and review: the author and maintainer side."""

import hashlib
import os
import shutil
import stat
import unittest
import zipfile

from helpers import (
    FIXTURES,
    MAINTAINER,
    ToolTest,
    copy_fixture,
    read_json,
    run,
    tool,
    write_json,
    zip_names,
)

CHECK = tool("check")
RELEASE = MAINTAINER / "release.py"
REVIEW = MAINTAINER / "review.py"


def make_package(directory, slug):
    write_json(directory / "package.json",
               {"package": slug, "title": slug, "maintainers": ["domain-lead@example.com"], "version": "0.1.0"})
    return directory


def write_skill(package, dirname, name, *, example=True, changes=True, body=None):
    skill = package / "skills" / dirname
    skill.mkdir(parents=True)
    if body is None:
        body = (f'---\nname: {name}\ndescription: "Sample {name}."\nowner: domain-lead@example.com\n'
                f"data_sources: none\n---\n\n# {name}\n")
    (skill / "SKILL.md").write_text(body, encoding="utf-8")
    if example:
        (skill / "examples").mkdir()
        (skill / "examples/run.md").write_text("# Question\n\nOne.\n\n# Steps\n\nTwo.\n\n# Answer\n\nThree.\n",
                                               encoding="utf-8")
    if changes:
        (skill / "CHANGES.md").write_text("# Changes\n\n## 2026-10-10\n\nSample.\n", encoding="utf-8")
    return skill


def write_script(skill, name, text):
    (skill / "scripts").mkdir(exist_ok=True)
    (skill / "scripts" / name).write_text(text, encoding="utf-8")


class CheckTest(ToolTest):
    def test_fixtures_pass(self):
        foundation = run(CHECK, "--package", FIXTURES / "foundation-sample")
        self.assertEqual(foundation.returncode, 0, foundation.stdout)
        self.assertIn("0 blocking, 1 warnings", foundation.stdout)
        self.assertIn("no tests/ for a script", foundation.stdout)
        domain = run(CHECK, "--package", FIXTURES / "domain-sample")
        self.assertEqual(domain.returncode, 0, domain.stdout)
        self.assertIn("0 blocking, 0 warnings", domain.stdout)
        self.assertIn("domain-lead@example.com", domain.stdout)

    def test_broken_structure_blocks(self):
        report = run(CHECK, "--package", self.broken_package())
        self.assertEqual(report.returncode, 1, report.stdout)
        for phrase in (
            "missing frontmatter",
            "frontmatter missing owner",
            "no example",
            "no CHANGES.md entry",
            "dependency range tabulate>=0.9",
            "no parseable PEP 723 block",
            "skill name duplicate-skill collides",
            "reserved skill name sync",
            "more than 64 files",
            "over 64 KiB",
            "binary",
            "symlink",
            "conflict copy",
            "credential-like file",
            "executable bit set",
        ):
            self.assertIn(phrase, report.stdout, phrase)

    def test_risky_code_only_warns(self):
        package = make_package(self.tmp / "warning-sample", "warning-sample")
        skill = write_skill(package, "warn-script", "warn-script")
        write_script(skill, "use.py", "\n".join([
            "# /// script",
            '# requires-python = ">=3.9"',
            '# dependencies = ["tabulate==0.10.0"]',
            "# ///",
            "import os, socket, requests, urllib.request, subprocess",
            "eval('1')",
            "exec('1')",
            "os.system('true')",
            "open('/tmp/aidist-check', 'w')",
            "",
        ]))
        (skill / "tests").mkdir()
        (skill / "tests/test_fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
        report = run(CHECK, "--package", package)
        self.assertEqual(report.returncode, 0, report.stdout)
        for phrase in (
            "imports socket",
            "imports requests",
            "imports urllib",
            "imports subprocess",
            "calls eval",
            "calls exec",
            "calls os.system",
            "writes outside the working directory",
            "third-party dependency tabulate==0.10.0",
            "tests failed",
        ):
            self.assertIn(phrase, report.stdout, phrase)

        grown = copy_fixture(FIXTURES / "domain-sample", self.tmp / "grown", "grown-sample")
        (grown / "skills/block-notes/notes.txt").write_text("x" * 5000, encoding="utf-8")
        size = run(CHECK, "--package", grown, "--baseline", FIXTURES / "domain-sample")
        self.assertEqual(size.returncode, 0, size.stdout)
        self.assertIn("large size increase", size.stdout)

    def broken_package(self):
        package = make_package(self.tmp / "broken-samples", "broken-samples")
        write_skill(package, "missing-frontmatter", "missing-frontmatter", body="# no frontmatter\n")
        write_skill(package, "bad-frontmatter", "bad-frontmatter",
                    body='---\nname: bad-frontmatter\ndescription: "Missing owner."\ndata_sources: none\n---\n')
        write_skill(package, "no-example", "no-example", example=False)
        write_skill(package, "no-changes", "no-changes", changes=False)
        write_script(write_skill(package, "range-pin", "range-pin"), "use.py",
                     '# /// script\n# dependencies = ["tabulate>=0.9"]\n# ///\nprint("x")\n')
        write_script(write_skill(package, "bare-script", "bare-script"), "run.py", "print('x')\n")
        write_skill(package, "same-name-a", "duplicate-skill")
        write_skill(package, "same-name-b", "duplicate-skill")
        write_skill(package, "sync", "sync")
        wide = write_skill(package, "wide-skill", "wide-skill")
        for number in range(70):
            (wide / f"file-{number}.txt").write_text("x\n", encoding="utf-8")
        (write_skill(package, "huge-skill", "huge-skill") / "notes.txt").write_bytes(b"a" * (64 * 1024 + 1))
        (write_skill(package, "binary-skill", "binary-skill") / "notes.txt").write_bytes(b"hello\0")
        os.symlink("SKILL.md", write_skill(package, "linked-skill", "linked-skill") / "link.md")
        (write_skill(package, "conflict-skill", "conflict-skill") / "notes (1).md").write_text("copy\n")
        (write_skill(package, "secret-skill", "secret-skill") / ".env").write_text("TOKEN=1\n")
        marked = write_skill(package, "exec-skill", "exec-skill") / "examples/run.md"
        marked.chmod(marked.stat().st_mode | stat.S_IXUSR)
        return package


class ReleaseTest(ToolTest):
    def test_framework_and_content_zips_match_their_manifests(self):
        out = self.tmp / "dist"
        self.release(out, min_version="0.0.1")
        framework_zip = out / "skills-hub/skills-hub-0.1.0.zip"
        self.assert_zip_matches_manifest(framework_zip, out / "skills-hub/manifest.json")
        current = read_json(out / "skills-hub/current.json")
        self.assertEqual(current["min_version"], "0.0.1")
        self.assertIsNone(current["zip_file_id"])
        self.assertEqual(current["zip_sha256"], hashlib.sha256(framework_zip.read_bytes()).hexdigest())
        names = zip_names(framework_zip)
        for name in ("tools/install.py", "tools/link.py", "skills/sync/SKILL.md", "templates/skill/SKILL.md",
                     "hooks/hooks.json"):
            self.assertIn(name, names)
        self.assertFalse(any("__pycache__" in name for name in names))

        for slug in ("foundation-sample", "domain-sample"):
            self.release(out, FIXTURES / slug)
            self.assert_zip_matches_manifest(out / slug / f"{slug}-0.1.0.zip", out / slug / "manifest.json")
            self.assertNotIn("tools/install.py", zip_names(out / slug / f"{slug}-0.1.0.zip"))

    def test_small_zips_are_padded_the_same_way_every_time(self):
        first, second = self.tmp / "first", self.tmp / "second"
        for out in (first, second):
            self.release(out, FIXTURES / "domain-sample")
        zip_path = first / "domain-sample/domain-sample-0.1.0.zip"
        self.assertGreaterEqual(zip_path.stat().st_size, 64 * 1024)
        self.assertEqual(zip_path.read_bytes(), (second / "domain-sample/domain-sample-0.1.0.zip").read_bytes())
        with zipfile.ZipFile(zip_path) as archive:
            padding = archive.getinfo("padding.bin")
            self.assertEqual(padding.compress_type, zipfile.ZIP_STORED)
        listed = {entry["path"] for entry in read_json(first / "domain-sample/manifest.json")["files"]}
        self.assertNotIn("padding.bin", listed)

        reserved = copy_fixture(FIXTURES / "domain-sample", self.tmp / "reserved", "reserved")
        (reserved / "padding.bin").write_bytes(b"x")
        refused = run(RELEASE, "--dry-run", "--package", reserved, "--out", self.tmp / "refused")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("padding.bin is reserved", refused.stderr)

    def test_refuses_broken_packages_and_a_content_installer(self):
        broken = make_package(self.tmp / "broken", "broken")
        write_skill(broken, "no-example", "no-example", example=False)
        refused = run(RELEASE, "--dry-run", "--package", broken, "--out", self.tmp / "refused")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("refusing release", refused.stderr)
        self.assertFalse((self.tmp / "refused").exists())

        smuggled = copy_fixture(FIXTURES / "domain-sample", self.tmp / "smuggled", "smuggled")
        (smuggled / "tools").mkdir()
        (smuggled / "tools/install.py").write_text("print('x')\n", encoding="utf-8")
        refused = run(RELEASE, "--dry-run", "--package", smuggled, "--out", self.tmp / "refused")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("content zip contains tools/install.py", refused.stderr)

        impostor = copy_fixture(FIXTURES / "domain-sample", self.tmp / "impostor", "skills-hub")
        refused = run(RELEASE, "--dry-run", "--package", impostor, "--out", self.tmp / "refused")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("skills-hub is the framework's slug", refused.stderr)
        self.assertFalse((self.tmp / "refused").exists())

    def assert_zip_matches_manifest(self, zip_path, manifest_path):
        manifest = read_json(manifest_path)
        with zipfile.ZipFile(zip_path) as archive:
            self.assertIn("manifest.json", archive.namelist())
            for entry in manifest["files"]:
                data = archive.read(entry["path"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertEqual(len(data), entry["bytes"])


class AuthoringTest(ToolTest):
    def test_draft_fills_a_package_and_a_skill_that_checks(self):
        package = self.tmp / "orchard"
        drafted = run(tool("draft"), "package", "--dest", package, "--package", "orchard",
                      "--title", "Orchard", "--maintainer", "grower@example.com")
        self.assertEqual(drafted.returncode, 0, drafted.stderr)
        skill = run(tool("draft"), "skill", "--dest", package / "skills/harvest", "--package", "orchard",
                    "--skill", "harvest", "--owner", "grower@example.com",
                    "--description", "Use when the user says harvest.")
        self.assertEqual(skill.returncode, 0, skill.stderr)
        text = (package / "skills/harvest/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: harvest", text)
        self.assertIn("~/.skills-hub/packages/orchard/current/skills/harvest/scripts/run.py", text)
        checked = run(CHECK, "--package", package)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertIn("0 blocking, 0 warnings", checked.stdout)

    def test_publish_writes_a_zip_and_refuses_a_broken_skill(self):
        package = self.tmp / "domain"
        shutil.copytree(FIXTURES / "domain-sample", package)
        inbox = self.tmp / "inbox"

        def publish(rationale):
            return run(tool("publish"), "--package-dir", package, "--skill", "block-notes",
                       "--rationale", rationale, "--author", "other@example.com", "--out", inbox)

        published = publish("Note a row.")
        self.assertEqual(published.returncode, 0, published.stderr)
        self.assertIn("submission package=domain-sample skill=block-notes", published.stdout)
        zips = list(inbox.glob("*.zip"))
        self.assertEqual(len(zips), 1)
        self.assertTrue(zips[0].name.startswith("block-notes__"))
        self.assertTrue(zips[0].name.endswith("__other.zip"))
        self.assertIn("Note a row.", (package / "skills/block-notes/CHANGES.md").read_text(encoding="utf-8"))
        submission = read_json(package / "skills/block-notes/submission.json")
        self.assertEqual(submission["submitter"], "other@example.com")
        self.assertEqual(submission["package"], "domain-sample")

        shutil.rmtree(package / "skills/block-notes/examples")
        refused = publish("This should not ship.")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("no example", refused.stderr)
        self.assertEqual(len(list(inbox.glob("*.zip"))), 1)
        self.assertNotIn("This should not ship.", (package / "skills/block-notes/CHANGES.md").read_text())

    def test_review_shows_diff_owner_and_drive_fields(self):
        package = self.tmp / "submission"
        shutil.copytree(FIXTURES / "foundation-sample", package)
        skill = package / "skills/shared-terms"
        (skill / "SKILL.md").write_text(
            (skill / "SKILL.md").read_text(encoding="utf-8").replace("SHARED-TERMS-SKILL-LOADED", "EDITED-MARKER"),
            encoding="utf-8",
        )
        write_json(skill / "submission.json", {"package": "foundation-sample", "skill": "shared-terms",
                                               "submitter": "other@example.com", "rationale": "Clarify the marker."})
        report = run(REVIEW, "--package", package, "--skill", "shared-terms",
                     "--baseline", FIXTURES / "foundation-sample",
                     "--drive-owner", "drive-user@example.com", "--drive-modifier", "drive-user@example.com")
        self.assertEqual(report.returncode, 0, report.stdout)
        for phrase in ("owner: r&d@example.com", "submitter: other@example.com", "rationale: Clarify the marker.",
                       "drive owner: drive-user@example.com", "drive last modifier: drive-user@example.com",
                       "-1. Reply with the marker `SHARED-TERMS-SKILL-LOADED`.",
                       "+1. Reply with the marker `EDITED-MARKER`.", "0 blocking"):
            self.assertIn(phrase, report.stdout, phrase)

        shutil.rmtree(skill / "examples")
        broken = run(REVIEW, "--package", package, "--skill", "shared-terms",
                     "--baseline", FIXTURES / "foundation-sample")
        self.assertEqual(broken.returncode, 1, broken.stdout)
        self.assertIn("no example", broken.stdout)
        self.assertIn("drive owner: unknown", broken.stdout)


if __name__ == "__main__":
    unittest.main()
