"""doctor, stale, and link: what the user's machine reports and loads."""

import shutil
import unittest
from datetime import datetime, timedelta, timezone

from helpers import ROOT, FIXTURES, ToolTest, copy_fixture, read_json, run, snapshot, tool, write_json

DOCTOR = tool("doctor")
STALE = tool("stale")
LINK = tool("link")


class DoctorStaleTest(ToolTest):
    def test_stale_reminder_and_cross_package_collision(self):
        out, root = self.tmp / "dist", self.tmp / "skills-hub"
        for slug in ("domain-sample", "foundation-sample"):
            self.release(out, FIXTURES / slug)
            self.install_release(root, out / slug)

        quiet = run(STALE, "--root", root)
        self.assertEqual(quiet.returncode, 0, quiet.stderr)
        self.assertEqual(quiet.stdout, "")
        healthy = run(DOCTOR, "--root", root)
        self.assertEqual(healthy.returncode, 0, healthy.stdout)
        self.assertIn("skills-hub: not installed", healthy.stdout)
        self.assertIn("package domain-sample 0.1.0 maintainers domain-lead@example.com", healthy.stdout)
        self.assertIn("package foundation-sample 0.1.0 maintainers r&d@example.com", healthy.stdout)
        self.assertTrue(healthy.stdout.endswith("ok\n"))

        state = read_json(root / "state.json")
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        state["packages"]["domain-sample"]["last_check"] = old.isoformat().replace("+00:00", "Z")
        write_json(root / "state.json", state)
        reminder = run(STALE, "--root", root)
        self.assertIn("sync: packages are stale and their scripts will not run until synced: domain-sample",
                      reminder.stdout)
        self.assertNotIn("foundation-sample", reminder.stdout)

        collision = copy_fixture(FIXTURES / "foundation-sample", self.tmp / "collision", "collision-sample",
                                 ["other@example.com"])
        self.release(out, collision)
        before = snapshot(root / "packages" / "foundation-sample")
        self.install_release(root, out / "collision-sample")
        diagnosed = run(DOCTOR, "--root", root)
        self.assertEqual(diagnosed.returncode, 1, diagnosed.stdout)
        self.assertIn("collision: shared-terms loaded from foundation-sample", diagnosed.stdout)
        self.assertIn("blocked: collision-sample shared-terms", diagnosed.stdout)
        self.assertEqual(snapshot(root / "packages" / "foundation-sample"), before)


class LinkTest(ToolTest):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "skills-hub"
        self.skills = self.tmp / "cursor-skills"
        self.skills.mkdir(parents=True)
        self.packages = {}

    def plant(self, slug, source, last_check="2026-10-10T00:00:00Z", maintainers=None):
        """Place a package as if installed, without going through install.py."""
        current = self.root / "packages" / slug / "current"
        copy_fixture(source, current, slug, maintainers)
        self.packages[slug] = {"version": "0.1.0", "last_check": last_check}
        write_json(self.root / "state.json", {"packages": self.packages})
        return current

    def link(self, *extra):
        result = run(LINK, "--root", self.root, "--skills-dir", self.skills, *extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_links_are_owned_and_a_blocked_skill_is_left_out(self):
        self.plant("foundation-sample", FIXTURES / "foundation-sample")
        self.plant("domain-sample", FIXTURES / "domain-sample")
        self.plant("taken", FIXTURES / "domain-sample", maintainers=["a@example.com"])
        shutil.copytree(ROOT / "framework", self.root / "framework" / "current")
        (self.skills / "keep-me").write_text("leave this\n", encoding="utf-8")
        (self.skills / "taken").write_text("not a link\n", encoding="utf-8")

        linked = self.link()
        self.assertIn("linked foundation-sample", linked)
        self.assertIn("linked domain-sample", linked)
        self.assertIn(f"left {self.skills / 'taken'} in place", linked)
        foundation, domain = self.skills / "foundation-sample", self.skills / "domain-sample"
        self.assertEqual(foundation.resolve(), (self.root / "packages/foundation-sample/current").resolve())
        self.assertEqual(domain.resolve(), (self.root / "packages/domain-sample/current").resolve())
        self.assertEqual((self.skills / "skills-hub").resolve(), (self.root / "framework/current").resolve())
        self.assertEqual((self.skills / "keep-me").read_text(encoding="utf-8"), "leave this\n")
        self.assertEqual((self.skills / "taken").read_text(encoding="utf-8"), "not a link\n")

        self.link("--unlink", "domain-sample")
        self.assertFalse(domain.exists())
        self.assertTrue(foundation.is_symlink())
        markers = read_json(self.root / "links.json")["packages"]
        self.assertNotIn("domain-sample", markers)
        self.assertIn("foundation-sample", markers)

        before = (foundation / "skills/shared-terms/SKILL.md").read_text(encoding="utf-8")
        self.plant("collision-sample", FIXTURES / "foundation-sample", "2026-10-10T02:00:00Z", ["other@example.com"])
        again = self.link()
        self.assertIn("linked collision-sample without shared-terms", again)
        self.assertFalse((self.skills / "collision-sample/skills/shared-terms").exists())
        self.assertEqual((foundation / "skills/shared-terms/SKILL.md").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
