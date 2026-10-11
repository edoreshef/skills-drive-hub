"""setup_drive.py and release.py --upload against an in-memory Drive: the layout, the fixed-ID pointer files, the
hash check before current.json moves, the refusal to re-release a version, and index.json / START HERE upkeep."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, MAINTAINER, ROOT

sys.path.insert(0, str(MAINTAINER))
sys.path.insert(0, str(ROOT / "framework" / "tools"))


class FakeDrive:
    """Just enough of maintainer/drive.Drive: files with parents, shared drives, media updates, checksums."""

    def __init__(self, corrupt_uploads=False):
        self.files, self.drives, self.n, self.corrupt = {}, [], 0, corrupt_uploads

    def _id(self):
        self.n += 1
        return f"id{self.n:03d}"

    def about(self):
        return {"user": {"emailAddress": "maintainer@example.com"}}

    def list_drives(self):
        return list(self.drives)

    def create_drive(self, name):
        for d in self.drives:
            if d["name"] == name:
                return d
        d = {"id": self._id(), "name": name}
        self.drives.append(d)
        return d

    def children(self, parent_id, name=None, drive_id=None):
        return [f for f in self.files.values() if f["parents"] == [parent_id] and (name is None or f["name"] == name)]

    def create_folder(self, name, parent_id):
        found = [f for f in self.children(parent_id, name) if f["mimeType"] == "application/vnd.google-apps.folder"]
        if found:
            return found[0]
        f = {"id": self._id(), "name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        self.files[f["id"]] = f
        return f

    def upload(self, name, parent_id, data, mime=None, convert_to=None):
        stored = data[:-1] + b"X" if self.corrupt and mime == "application/zip" else data
        f = {"id": self._id(), "name": name, "mimeType": convert_to or mime, "parents": [parent_id], "data": stored,
             "size": str(len(stored)), "sha256Checksum": hashlib.sha256(stored).hexdigest()}
        self.files[f["id"]] = f
        return f

    def update_media(self, file_id, data, mime="application/octet-stream"):
        f = self.files[file_id]
        f.update(data=data, size=str(len(data)), sha256Checksum=hashlib.sha256(data).hexdigest())
        return f

    def download(self, file_id):
        return self.files[file_id]["data"]


class DriveReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["SKILLS_HUB_REGISTRY"] = str(Path(self.tmp.name) / "drives.json")
        import importlib
        import drive as drive_mod
        importlib.reload(drive_mod)
        import setup_drive as sd
        importlib.reload(sd)
        import release
        importlib.reload(release)
        self.sd, self.release, self.drive_mod = sd, release, drive_mod
        self.fake = FakeDrive()
        self.registry = {"account": "maintainer@example.com", "hub": {}, "packages": {}}

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("SKILLS_HUB_REGISTRY", None)

    def _release(self, package_dir, framework=False, fake=None):
        out = Path(self.tmp.name) / "dist"
        argv = ["--dry-run", "--out", str(out)] + ([] if framework else ["--package", str(package_dir)])
        self.assertEqual(self.release.main(argv), 0)
        slug = "skills-hub" if framework else json.loads((package_dir / "package.json").read_text())["package"]
        dest = out / slug
        current = json.loads((dest / "current.json").read_text())
        zip_path = next(dest.glob("*.zip"))
        return self.release.upload(slug, current["version"], zip_path, current, dest, framework,
                                   drive=fake or self.fake, registry=self.registry)

    def test_hub_then_package_then_releases(self):
        self.sd.setup_hub(self.fake, self.registry, my_drive=False)
        hub = self.registry["hub"]
        self.assertEqual([d["name"] for d in self.fake.drives], ["Skills Hub — Published"])
        self.assertEqual(hub["published_root"], hub["published_drive"])
        for key in ("releases", "index_json", "start_here"):
            self.assertIn(key, hub)
        self.assertIn("<not released yet>", self.fake.files[hub["start_here"]]["data"].decode())

        # the framework release fills the START HERE placeholders and keeps current.json's ID on a re-release
        self.assertEqual(self._release(None, framework=True), 0)
        first_pointer = hub["current_json"]
        start = self.fake.files[hub["start_here"]]["data"].decode()
        self.assertIn(first_pointer, start)
        self.assertIn(hub["index_json"], start)
        self.assertNotIn("<SKILLS_HUB_CURRENT_JSON_ID>", start)
        self.assertNotIn("<INDEX_JSON_ID>", start)
        self.assertNotIn("not released yet", start.split("## Packages")[0])

        # a content package: two drives, the submission folders, an index.json entry
        pkg = FIXTURES / "domain-sample"
        self.sd.setup_package(self.fake, self.registry, pkg, my_drive=False)
        slug = json.loads((pkg / "package.json").read_text())["package"]
        p = self.registry["packages"][slug]
        names = [d["name"] for d in self.fake.drives]
        self.assertIn(f"{p['title']} — Published", names)
        self.assertIn(f"{p['title']} — Submissions", names)
        self.assertEqual(sorted(k for k in p["submissions"] if k not in ("root", "drive")),
                         ["accepted", "feedback", "inbox", "rejected"])
        index = json.loads(self.fake.files[hub["index_json"]]["data"])
        self.assertEqual([e["slug"] for e in index["packages"]], [slug])
        self.assertIsNone(index["packages"][0]["current_file_id"])

        self.assertEqual(self._release(pkg), 0)
        index = json.loads(self.fake.files[hub["index_json"]]["data"])
        self.assertEqual(index["packages"][0]["current_file_id"], p["current_json"])
        pointer = json.loads(self.fake.files[p["current_json"]]["data"])
        zip_file = self.fake.files[pointer["zip_file_id"]]
        self.assertEqual(zip_file["parents"], [p["releases"]])
        self.assertEqual(hashlib.sha256(zip_file["data"]).hexdigest(), pointer["zip_sha256"])
        self.assertIn(p["current_json"], self.fake.files[p["start_here"]]["data"].decode())
        self.assertIn(slug, self.fake.files[hub["start_here"]]["data"].decode())

        # the same version again is refused, and nothing moved
        with self.assertRaises(RuntimeError):
            self._release(pkg)
        self.assertEqual(json.loads(self.fake.files[p["current_json"]]["data"]), pointer)

        # the registry was saved without credentials
        saved = json.loads(Path(os.environ["SKILLS_HUB_REGISTRY"]).read_text())
        self.assertEqual(saved["packages"][slug]["current_json"], p["current_json"])
        self.assertNotIn("token", json.dumps(saved).lower())

    def test_a_bad_upload_never_moves_current_json(self):
        self.sd.setup_hub(self.fake, self.registry, my_drive=True)
        self.assertIsNone(self.registry["hub"].get("published_drive"), "My Drive: folders, no shared drive")
        corrupt = FakeDrive(corrupt_uploads=True)
        corrupt.files, corrupt.n = self.fake.files, self.fake.n
        with self.assertRaises(RuntimeError) as ctx:
            self._release(None, framework=True, fake=corrupt)
        self.assertIn("different bytes", str(ctx.exception))
        self.assertNotIn("current_json", self.registry["hub"])
        self.assertEqual(self.fake.children(self.registry["hub"]["published_root"], "current.json"), [])


if __name__ == "__main__":
    unittest.main()
