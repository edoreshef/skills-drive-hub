"""install.py and sync.py: both download forms install, and a refusal changes nothing."""

import shutil
import unittest

from helpers import FIXTURES, ToolTest, read_json, run, sha256, snapshot, tool, write_json, zip_tree

INSTALL = tool("install")
SYNC = tool("sync")


class InstallTest(ToolTest):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "skills-hub"
        self.domain_zip = zip_tree(FIXTURES / "domain-sample")
        self.foundation_zip = zip_tree(FIXTURES / "foundation-sample")

    def install(self, slug, digest, source_flag, source_path, *extra, root=None):
        return run(INSTALL, "--package", slug, "--sha256", digest, source_flag, source_path,
                   "--root", root or self.root, *extra)

    def test_both_downloads_install_and_a_flipped_byte_changes_nothing(self):
        domain = self.install(
            "domain-sample", sha256(self.domain_zip), "--base64-file", self.write_base64("d.b64", self.domain_zip),
            "--bytes", len(self.domain_zip), "--version", "0.1.0", "--current-file-id", "domain-file",
        )
        self.assertEqual(domain.returncode, 0, domain.stderr)
        self.assertIn("package=domain-sample", domain.stdout)
        domain_tree = snapshot(self.root / "packages" / "domain-sample")
        self.assertIn("current/skills/block-notes/SKILL.md", domain_tree)
        self.assertNotIn("staging", {path.split("/")[0] for path in domain_tree})

        state = read_json(self.root / "state.json")
        state["framework"] = {"version": "0"}
        write_json(self.root / "state.json", state)
        domain_record = state["packages"]["domain-sample"]
        self.assertEqual(domain_record["version"], "0.1.0")
        self.assertEqual(domain_record["current_file_id"], "domain-file")

        foundation = self.install(
            "foundation-sample", sha256(self.foundation_zip), "--from-tool-result",
            self.write_tool_result("f.txt", self.foundation_zip), "--bytes", len(self.foundation_zip),
        )
        self.assertEqual(foundation.returncode, 0, foundation.stderr)
        self.assertEqual(snapshot(self.root / "packages" / "domain-sample"), domain_tree)
        script = self.root / "packages/foundation-sample/current/skills/shared-terms/scripts/echo_marker.py"
        ran = run(script)
        self.assertEqual(ran.stdout.strip(), "SHARED-TERMS-SCRIPT-RAN")
        state = read_json(self.root / "state.json")
        self.assertEqual(state["framework"], {"version": "0"})
        self.assertEqual(state["packages"]["domain-sample"], domain_record)

        again = self.install("domain-sample", sha256(self.domain_zip), "--from-tool-result",
                             self.write_tool_result("d.txt", self.domain_zip))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertTrue((self.root / "packages/domain-sample/previous/package.json").is_file())
        self.assertFalse((self.root / "packages/domain-sample/staging").exists())
        self.assertEqual(read_json(self.root / "state.json")["packages"]["domain-sample"]["current_file_id"],
                         "domain-file")

        before = snapshot(self.root / "packages")
        flipped = bytearray(self.foundation_zip)
        flipped[-1] ^= 0xFF
        refused = self.install("foundation-sample", sha256(self.foundation_zip), "--base64-file",
                               self.write_base64("flipped.b64", bytes(flipped)))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("sha256 mismatch", refused.stderr)
        self.assertIn("unchanged", refused.stderr)
        self.assertEqual(snapshot(self.root / "packages"), before)

    def test_mismatch_on_a_fresh_root_writes_nothing(self):
        flipped = bytearray(self.domain_zip)
        flipped[-1] ^= 0xFF
        fresh = self.tmp / "fresh"
        refused = self.install("domain-sample", sha256(self.domain_zip), "--base64-file",
                               self.write_base64("bad.b64", bytes(flipped)), root=fresh)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("nothing written", refused.stderr)
        self.assertFalse(fresh.exists())

    def test_package_field_must_match_the_slug(self):
        self.install("domain-sample", sha256(self.domain_zip), "--base64-file",
                     self.write_base64("d.b64", self.domain_zip))
        before = snapshot(self.root)
        refused = self.install("foundation-sample", sha256(self.domain_zip), "--from-tool-result",
                               self.write_tool_result("wrong.txt", self.domain_zip))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("package.json says", refused.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_slug_cannot_escape_the_root(self):
        fresh = self.tmp / "fresh"
        refused = self.install("../outside", sha256(self.domain_zip), "--base64-file",
                               self.write_base64("d.b64", self.domain_zip), root=fresh)
        self.assertNotEqual(refused.returncode, 0)
        self.assertFalse(fresh.exists())
        self.assertFalse((self.tmp / "outside").exists())

    def test_damaged_state_refuses_before_swapping(self):
        self.install("domain-sample", sha256(self.domain_zip), "--base64-file",
                     self.write_base64("d.b64", self.domain_zip))
        (self.root / "state.json").write_text("{not json", encoding="utf-8")
        before = snapshot(self.root / "packages")
        refused = self.install("domain-sample", sha256(self.domain_zip), "--base64-file",
                               self.write_base64("d2.b64", self.domain_zip))
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("state.json is not JSON", refused.stderr)
        self.assertEqual(snapshot(self.root / "packages"), before)


class SyncTest(ToolTest):
    def test_sync_updates_one_package_and_stops_below_min_version(self):
        out, root = self.tmp / "dist", self.tmp / "skills-hub"
        for slug in ("foundation-sample", "domain-sample"):
            self.release(out, FIXTURES / slug)
            self.install_release(root, out / slug)
        domain_tree = snapshot(root / "packages" / "domain-sample")
        domain_record = read_json(root / "state.json")["packages"]["domain-sample"]
        self.assertIn("current/manifest.json", domain_tree)
        self.assertNotIn("current/padding.bin", domain_tree)

        bumped = self.tmp / "foundation-v2"
        shutil.copytree(FIXTURES / "foundation-sample", bumped)
        write_json(bumped / "package.json", {**read_json(bumped / "package.json"), "version": "0.2.0"})
        (bumped / "skills/shared-terms/MARKER.txt").write_text("v2\n", encoding="utf-8")
        self.release(out, bumped, min_version="0.2.0")
        release_dir = out / "foundation-sample"

        synced = run(SYNC, "--root", root, "--from-release", release_dir)
        self.assertEqual(synced.returncode, 0, synced.stderr)
        self.assertIn("package=foundation-sample version=0.2.0", synced.stdout)
        self.assertEqual((root / "packages/foundation-sample/current/skills/shared-terms/MARKER.txt").read_text(), "v2\n")
        self.assertEqual(snapshot(root / "packages" / "domain-sample"), domain_tree)
        state = read_json(root / "state.json")
        self.assertEqual(state["packages"]["domain-sample"], domain_record)
        foundation_tree = snapshot(root / "packages" / "foundation-sample")
        foundation_check = state["packages"]["foundation-sample"]["last_check"]

        again = run(SYNC, "--root", root, "--from-release", release_dir)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("up to date package=foundation-sample version=0.2.0", again.stdout)
        self.assertEqual(snapshot(root / "packages" / "foundation-sample"), foundation_tree)
        self.assertNotEqual(read_json(root / "state.json")["packages"]["foundation-sample"]["last_check"],
                            foundation_check)

        stalled = self.tmp / "stalled.json"
        write_json(stalled, {**read_json(release_dir / "current.json"), "min_version": "0.9.0"})
        before = snapshot(root / "packages")
        refused = run(SYNC, "--root", root, "--current", stalled, "--zip", release_dir / "foundation-sample-0.2.0.zip")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("below min_version", refused.stderr)
        self.assertIn("sync required before using content skills", refused.stderr)
        self.assertEqual(snapshot(root / "packages"), before)

        flipped = self.tmp / "bad-release"
        shutil.copytree(out / "domain-sample", flipped)
        blob = bytearray((flipped / "domain-sample-0.1.0.zip").read_bytes())
        blob[-1] ^= 0xFF
        (flipped / "domain-sample-0.1.1.zip").write_bytes(bytes(blob))
        write_json(flipped / "current.json", {**read_json(flipped / "current.json"), "version": "0.1.1"})
        bad = run(SYNC, "--root", root, "--from-release", flipped)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("sha256 mismatch", bad.stderr)
        self.assertEqual(snapshot(root / "packages"), before)

    def test_sync_takes_connector_downloads(self):
        out, root = self.tmp / "dist", self.tmp / "skills-hub"
        for slug in ("foundation-sample", "domain-sample"):
            self.release(out, FIXTURES / slug)
            self.install_release(root, out / slug)
        domain_dir = out / "domain-sample"
        domain_tree = snapshot(root / "packages" / "domain-sample")

        same = run(SYNC, "--root", root, "--current",
                   self.write_tool_result("d-current.txt", (domain_dir / "current.json").read_bytes(), nested=True))
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertIn("up to date package=domain-sample version=0.1.0", same.stdout)

        bumped = self.tmp / "foundation-v2"
        shutil.copytree(FIXTURES / "foundation-sample", bumped)
        for version in ("0.2.0", "0.3.0"):
            write_json(bumped / "package.json", {**read_json(bumped / "package.json"), "version": version})
            (bumped / "skills/shared-terms/MARKER.txt").write_text(f"{version}\n", encoding="utf-8")
            self.release(out, bumped)
            release_dir = out / "foundation-sample"
            current = (release_dir / "current.json").read_bytes()
            archive = (release_dir / f"foundation-sample-{version}.zip").read_bytes()
            if version == "0.2.0":
                current_file = self.write_tool_result("f-current.txt", current, file_id="foundation-current",
                                                      nested=True)
                zip_file = self.write_tool_result("f-zip.txt", archive, file_id="foundation-zip")
            else:
                current_file = self.write_base64("f-current.b64", current)
                zip_file = self.write_base64("f-zip.b64", archive)
            synced = run(SYNC, "--root", root, "--current", current_file, "--zip", zip_file)
            self.assertEqual(synced.returncode, 0, synced.stderr)
            self.assertIn(f"package=foundation-sample version={version}", synced.stdout)
            marker = root / "packages/foundation-sample/current/skills/shared-terms/MARKER.txt"
            self.assertEqual(marker.read_text(), f"{version}\n")
            record = read_json(root / "state.json")["packages"]["foundation-sample"]
            self.assertEqual(record["current_file_id"], "foundation-current")
        self.assertEqual(snapshot(root / "packages" / "domain-sample"), domain_tree)

        before, trees = snapshot(root), snapshot(root / "packages")
        garbage = self.tmp / "garbage.txt"
        garbage.write_text("the agent summarized the file instead of saving it\n", encoding="utf-8")
        refused = run(SYNC, "--root", root, "--current", garbage)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("is not a current.json", refused.stderr)
        self.assertEqual(snapshot(root), before)

        write_json(bumped / "package.json", {**read_json(bumped / "package.json"), "version": "0.4.0"})
        self.release(out, bumped)
        current_file = self.write_tool_result("f4-current.txt", (out / "foundation-sample/current.json").read_bytes())
        swapped = run(SYNC, "--root", root, "--current", current_file, "--zip", current_file)
        self.assertEqual(swapped.returncode, 1)
        self.assertIn("is not a zip", swapped.stderr)
        self.assertEqual(snapshot(root / "packages"), trees)
        self.assertEqual(read_json(root / "state.json")["packages"]["foundation-sample"]["pending_version"], "0.4.0")


if __name__ == "__main__":
    unittest.main()


class MarketplaceTest(unittest.TestCase):
    def test_install_writes_the_local_marketplace(self):
        """Claude Code registers <root> once; install.py keeps .claude-plugin/marketplace.json listing every tree."""
        import json
        import tempfile
        from pathlib import Path

        from helpers import FIXTURES, MAINTAINER, run, tool

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            out = Path(tmp) / "dist"
            self.assertEqual(run(MAINTAINER / "release.py", "--dry-run", "--package", FIXTURES / "domain-sample", "--out", out).returncode, 0)
            current = json.loads((out / "domain-sample" / "current.json").read_text())
            zip_path = next((out / "domain-sample").glob("*.zip"))
            b64 = Path(tmp) / "zip.b64"
            import base64
            b64.write_text(base64.b64encode(zip_path.read_bytes()).decode())
            result = run(tool("install"), "--package", "domain-sample", "--sha256", current["zip_sha256"], "--base64-file", b64, "--root", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
            self.assertEqual([p["name"] for p in market["plugins"]], ["domain-sample"])     # no framework tree yet
            self.assertEqual(market["plugins"][0]["source"], "./packages/domain-sample/current")
            # with a framework tree in place it is listed first
            fw = root / "framework" / "current" / ".claude-plugin"
            fw.mkdir(parents=True)
            (fw / "plugin.json").write_text(json.dumps({"name": "skills-hub", "version": "9.9.9", "description": "d"}))
            import sys
            sys.path.insert(0, str(tool("common").parent))
            from common import write_marketplace
            market = json.loads(write_marketplace(root).read_text())
            self.assertEqual([p["name"] for p in market["plugins"]], ["skills-hub", "domain-sample"])
            self.assertEqual(market["plugins"][0]["version"], "9.9.9")


class RawZipAndRootTest(unittest.TestCase):
    def test_from_tool_result_accepts_the_raw_zip_and_skills_hub_root_is_the_default(self):
        """Claude Science's kernel saves the zip's bytes, not the connector's JSON envelope; and its root comes
        from SKILLS_HUB_ROOT because ~ does not persist there."""
        import json
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        from helpers import FIXTURES, MAINTAINER, run, tool

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            self.assertEqual(run(MAINTAINER / "release.py", "--dry-run", "--package", FIXTURES / "domain-sample", "--out", out).returncode, 0)
            current = json.loads((out / "domain-sample" / "current.json").read_text())
            zip_path = next((out / "domain-sample").glob("*.zip"))
            root = Path(tmp) / "workspace" / ".skills-hub"
            env = dict(os.environ, SKILLS_HUB_ROOT=str(root), PYTHONSAFEPATH="1")
            result = subprocess.run([sys.executable, str(tool("install")), "--package", "domain-sample", "--sha256",
                                     current["zip_sha256"], "--from-tool-result", str(zip_path)],
                                    capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "state.json").exists(), "installed under SKILLS_HUB_ROOT with no --root")
            doctor = subprocess.run([sys.executable, str(tool("doctor"))], capture_output=True, text=True, env=env)
            self.assertIn("domain-sample 0.1.0", doctor.stdout)
