"""The sync gate in released scripts: when a script runs, and when it refuses."""

import os
import shutil
import subprocess
import sys
import unittest
import zipfile
from datetime import datetime, timedelta, timezone

from helpers import FIXTURES, MAINTAINER, ToolTest, copy_fixture, read_json, run, sha256, tool, write_json

SYNC = tool("sync")
STALE = tool("stale")
SLUG = "foundation-sample"
MARKER = "SHARED-TERMS-SCRIPT-RAN"
BLOCKED = 75

PLACED = '''\
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Placed docstring."""

from __future__ import annotations


def shout(text: str) -> str:
    return text.upper()


print(__doc__)
print(shout("placed-ran"))
'''

NESTED = '''\
# /// script
# requires-python = ">=3.9"
# ///
print("NESTED-RAN")
'''


def iso(moment):
    return moment.isoformat().replace("+00:00", "Z")


class GateTest(ToolTest):
    def setUp(self):
        super().setUp()
        self.out, self.root, self.home = self.tmp / "dist", self.tmp / "skills-hub", self.tmp / "home"
        self.home.mkdir()
        self.release(self.out, FIXTURES / SLUG)
        self.install_release(self.root, self.out / SLUG)
        self.script = self.root / f"packages/{SLUG}/current/skills/shared-terms/scripts/echo_marker.py"

    def run_script(self, script=None, home=None, hub_root=None):
        env = dict(os.environ, HOME=str(home or self.home))
        env.pop("SKILLS_HUB_ROOT", None)
        if hub_root:
            env["SKILLS_HUB_ROOT"] = str(hub_root)
        return subprocess.run([sys.executable, str(script or self.script)], capture_output=True, text=True, env=env)

    def set_record(self, root=None, **fields):
        path = (root or self.root) / "state.json"
        state = read_json(path)
        state["packages"][SLUG].update(fields)
        write_json(path, state)

    def assert_runs(self, result, marker=MARKER):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(marker, result.stdout)

    def assert_blocked(self, result, reason):
        self.assertEqual(result.returncode, BLOCKED, result.stdout + result.stderr)
        self.assertNotIn(MARKER, result.stdout)
        self.assertIn(f"blocked: package {SLUG}: {reason}", result.stderr)
        self.assertIn("Run the sync skill", result.stderr)

    def test_fresh_check_runs_and_an_old_or_future_check_blocks(self):
        self.assert_runs(self.run_script())
        now = datetime.now(timezone.utc)
        self.set_record(last_check=iso(now - timedelta(hours=23)))
        self.assert_runs(self.run_script())
        self.set_record(last_check=iso(now - timedelta(hours=25)))
        old = self.run_script()
        self.assert_blocked(old, "last sync check")
        self.assertIn("over 24h old", old.stderr)
        self.set_record(last_check=iso(now + timedelta(hours=1)))
        future = self.run_script()
        self.assert_blocked(future, "last sync check")
        self.assertIn("is in the future", future.stderr)
        self.assertIn(SLUG, run(STALE, "--root", self.root).stdout)
        self.set_record(last_check="yesterday")
        self.assert_blocked(self.run_script(), "no readable sync record")

    def test_pending_update_blocks_until_it_is_installed(self):
        bumped = self.tmp / "foundation-v2"
        shutil.copytree(FIXTURES / SLUG, bumped)
        write_json(bumped / "package.json", {**read_json(bumped / "package.json"), "version": "0.2.0"})
        self.release(self.out, bumped)
        release_dir = self.out / SLUG

        checked = run(SYNC, "--root", self.root, "--current", release_dir / "current.json")
        self.assertEqual(checked.returncode, 1)
        self.assertIn("zip required", checked.stderr)
        self.assertEqual(read_json(self.root / "state.json")["packages"][SLUG]["pending_version"], "0.2.0")
        self.assert_blocked(self.run_script(), "update 0.2.0 is available")
        self.assertIn(SLUG, run(STALE, "--root", self.root).stdout)

        synced = run(SYNC, "--root", self.root, "--from-release", release_dir)
        self.assertEqual(synced.returncode, 0, synced.stderr)
        record = read_json(self.root / "state.json")["packages"][SLUG]
        self.assertEqual(record["version"], "0.2.0")
        self.assertNotIn("pending_version", record)
        self.assert_runs(self.run_script())
        self.assertEqual(run(STALE, "--root", self.root).stdout, "")

        self.set_record(pending_version="0.3.0")
        self.assert_blocked(self.run_script(), "update 0.3.0 is available")
        same = run(SYNC, "--root", self.root, "--from-release", release_dir)
        self.assertIn("up to date", same.stdout)
        self.assertNotIn("pending_version", read_json(self.root / "state.json")["packages"][SLUG])
        self.assert_runs(self.run_script())

    def test_under_the_install_root_a_missing_record_blocks(self):
        home_root = self.home / ".skills-hub"
        home_root.mkdir()
        shutil.copy(self.root / "state.json", home_root / "state.json")
        state = read_json(self.root / "state.json")
        write_json(self.root / "state.json", {**state, "packages": {}})
        self.assert_blocked(self.run_script(), "no readable sync record")
        (self.root / "state.json").write_text("{not json", encoding="utf-8")
        self.assert_blocked(self.run_script(), "no readable sync record")
        (self.root / "state.json").unlink()
        self.assert_blocked(self.run_script(), "no readable sync record")

    def test_a_cursor_link_resolves_to_the_install_root(self):
        link = self.tmp / "cursor-skills" / SLUG
        link.parent.mkdir()
        link.symlink_to(self.root / "packages" / SLUG / "current", target_is_directory=True)
        linked = link / "skills/shared-terms/scripts/echo_marker.py"
        self.assert_runs(self.run_script(linked))
        self.set_record(last_check=iso(datetime.now(timezone.utc) - timedelta(days=2)))
        self.assert_blocked(self.run_script(linked), "last sync check")

    def test_outside_the_install_root(self):
        copy = self.tmp / "elsewhere" / "echo_marker.py"
        copy.parent.mkdir()
        shutil.copy(self.script, copy)

        science = self.run_script(copy)
        self.assert_runs(science)
        self.assertIn(f"warning: package {SLUG}: no ~/.skills-hub on this host and SKILLS_HUB_ROOT is not set", science.stderr)

        home_root = self.home / ".skills-hub"
        home_root.mkdir()
        shutil.copy(self.root / "state.json", home_root / "state.json")
        self.assert_runs(self.run_script(copy))
        self.set_record(home_root, last_check=iso(datetime.now(timezone.utc) - timedelta(days=2)))
        self.assert_blocked(self.run_script(copy), "last sync check")
        write_json(home_root / "state.json", {"packages": {}})
        self.assert_blocked(self.run_script(copy), "no readable sync record")

    def test_skills_hub_root_names_the_state_and_fails_closed(self):
        """Claude Science: ~ does not persist, so START HERE sets SKILLS_HUB_ROOT to a workspace path. A published
        skill's script (outside any install root) reads that state and blocks like any other host."""
        copy = self.tmp / "published" / "skills" / "shared-terms" / "scripts" / "echo_marker.py"
        copy.parent.mkdir(parents=True)
        shutil.copy(self.script, copy)
        workspace_root = self.tmp / "workspace" / ".skills-hub"
        # set but missing: fails closed, no warning-and-run
        self.assert_blocked(self.run_script(copy, hub_root=workspace_root), "no readable sync record")
        workspace_root.mkdir(parents=True)
        shutil.copy(self.root / "state.json", workspace_root / "state.json")
        fresh = self.run_script(copy, hub_root=workspace_root)
        self.assert_runs(fresh)
        self.assertNotIn("warning", fresh.stderr)
        self.set_record(workspace_root, pending_version="9.9.9")
        self.assert_blocked(self.run_script(copy, hub_root=workspace_root), "update 9.9.9 is available")

    def test_gate_placement_nested_scripts_and_an_untouched_source(self):
        package = copy_fixture(FIXTURES / SLUG, self.tmp / "placed-src", "placed-sample")
        scripts = package / "skills/shared-terms/scripts"
        (scripts / "placed.py").write_text(PLACED, encoding="utf-8")
        (scripts / "tools").mkdir()
        (scripts / "tools/nested.py").write_text(NESTED, encoding="utf-8")
        source = {path.name: sha256(path.read_bytes()) for path in scripts.rglob("*.py")}

        self.release(self.out, package)
        self.assertEqual({path.name: sha256(path.read_bytes()) for path in scripts.rglob("*.py")}, source)
        zip_path = self.out / "placed-sample/placed-sample-0.1.0.zip"
        with zipfile.ZipFile(zip_path) as archive:
            placed = archive.read("skills/shared-terms/scripts/placed.py").decode("utf-8")
            self.assertNotIn("_skills_hub_gate", archive.read("skills/shared-terms/SKILL.md").decode("utf-8"))
        self.assertLess(placed.index("from __future__ import annotations"), placed.index("def _skills_hub_gate"))
        self.assertLess(placed.index("del _skills_hub_gate"), placed.index("def shout"))
        self.assertTrue(placed.startswith('#!/usr/bin/env python3\n# /// script\n# requires-python = ">=3.9"\n'
                                          '# ///\n"""Placed docstring."""\n'))

        self.install_release(self.root, self.out / "placed-sample")
        installed = self.root / "packages/placed-sample/current/skills/shared-terms/scripts"
        ran = self.run_script(installed / "placed.py")
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertEqual(ran.stdout.split(), ["Placed", "docstring.", "PLACED-RAN"])
        self.assert_runs(self.run_script(installed / "tools/nested.py"), "NESTED-RAN")

        state = read_json(self.root / "state.json")
        state["packages"]["placed-sample"]["last_check"] = iso(datetime.now(timezone.utc) - timedelta(days=2))
        write_json(self.root / "state.json", state)
        nested = self.run_script(installed / "tools/nested.py")
        self.assertEqual(nested.returncode, BLOCKED)
        self.assertIn("blocked: package placed-sample", nested.stderr)

    def test_release_refuses_a_script_the_gate_pushes_over_64_kib(self):
        package = copy_fixture(FIXTURES / SLUG, self.tmp / "big-src", "big-sample")
        script = package / "skills/shared-terms/scripts/echo_marker.py"
        filler = "# " + "x" * 98 + "\n"
        text = script.read_text(encoding="utf-8")
        script.write_text(text + filler * ((64 * 1024 - len(text) - 200) // len(filler)), encoding="utf-8")
        refused = run(MAINTAINER / "release.py", "--dry-run", "--out", self.out, "--package", package)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("over 64 KiB with the sync gate", refused.stderr)
        self.assertFalse((self.out / "big-sample").exists())


if __name__ == "__main__":
    unittest.main()
