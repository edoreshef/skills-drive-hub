#!/usr/bin/env python3
"""Create and maintain the Drive side of Skills Hub: the Shared Drives, their folders, the START HERE docs and
index.json (design.md "Drive layout"). Idempotent: every command reuses what already exists by name.

Usage:
  setup_drive.py hub      --account EMAIL [--my-drive]         "Skills Hub — Published": releases/, index.json, START HERE
  setup_drive.py package  --package DIR   [--my-drive]         "<slug> — Published" (releases/, START HERE) and
                                                               "<slug> — Submissions" (inbox/ accepted/ rejected/ feedback/);
                                                               registers the package in index.json
  setup_drive.py start-here                                    rewrite every START HERE doc with the current file IDs
  setup_drive.py share    (--hub | --package SLUG) (--domain D | --user EMAIL) --role ROLE [--submissions]
                                                               reader for users; organizer for a maintainer
  setup_drive.py show                                          what the registry knows, and what Drive says

What it records: ~/.config/skills-hub/drives.json (names and IDs; no credentials). --my-drive puts folders in the
account's My Drive instead of Shared Drives (for an account that may not create Shared Drives, or a test).
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[0]
sys.path.insert(0, str(HERE))
from drive import GDOC, Drive, DriveError, load_registry, save_registry  # noqa: E402

HUB_TITLE = "Skills Hub"
PUBLISHED = "{title} — Published"
SUBMISSIONS = "{title} — Submissions"
SUBMISSION_FOLDERS = ("inbox", "accepted", "rejected", "feedback")


def main(argv):
    parser = argparse.ArgumentParser(description="The Drive side of Skills Hub.")
    parser.add_argument("--account", help="Google account for gcloud (saved in the registry on first use).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    hub = sub.add_parser("hub")
    hub.add_argument("--my-drive", action="store_true")
    pkg = sub.add_parser("package")
    pkg.add_argument("--package", required=True, type=Path, help="The content package's directory (package.json).")
    pkg.add_argument("--my-drive", action="store_true")
    sub.add_parser("start-here")
    share = sub.add_parser("share")
    who = share.add_mutually_exclusive_group(required=True)
    who.add_argument("--hub", action="store_true")
    who.add_argument("--package", dest="slug")
    to = share.add_mutually_exclusive_group(required=True)
    to.add_argument("--domain")
    to.add_argument("--user")
    share.add_argument("--role", required=True, choices=("reader", "commenter", "writer", "fileOrganizer", "organizer"))
    share.add_argument("--submissions", action="store_true", help="the Submissions drive instead of Published")
    share.add_argument("--notify", action="store_true")
    sub.add_parser("show")
    args = parser.parse_args(argv)

    registry = load_registry()
    if args.account:
        registry["account"] = args.account
    drive = Drive(registry.get("account"))
    try:
        if args.cmd == "hub":
            setup_hub(drive, registry, args.my_drive)
        elif args.cmd == "package":
            setup_package(drive, registry, args.package, args.my_drive)
        elif args.cmd == "start-here":
            refresh_start_here(drive, registry)
        elif args.cmd == "share":
            do_share(drive, registry, args)
        elif args.cmd == "show":
            show(drive, registry)
    except DriveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        save_registry(registry)
    return 0


# ---- building blocks -----------------------------------------------------------------------------------------------

def _root(drive, title, kind, my_drive):
    """A Shared Drive (or a My Drive folder) named "<title> — Published|Submissions"; returns (root_id, drive_id)."""
    name = (PUBLISHED if kind == "published" else SUBMISSIONS).format(title=title)
    if my_drive:
        folder = drive.create_folder(name, "root")
        return folder["id"], None
    d = drive.create_drive(name)
    return d["id"], d["id"]


def _json_file(drive, parent_id, name, payload, existing_id=None):
    """Create a JSON file, or rewrite it in place so its ID never changes."""
    data = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    if existing_id:
        try:
            return drive.update_media(existing_id, data, "application/json")
        except DriveError:
            pass                                    # gone: fall through and make a new one
    found = drive.children(parent_id, name)
    if found:
        return drive.update_media(found[0]["id"], data, "application/json")
    return drive.upload(name, parent_id, data, "application/json")


def _doc(drive, parent_id, name, markdown, existing_id=None):
    """A Google Doc from Markdown text, created once and rewritten in place after that."""
    data = markdown.encode("utf-8")
    target = existing_id or next((f["id"] for f in drive.children(parent_id, name) if f["mimeType"] == GDOC), None)
    if target:
        try:
            return drive.update_media(target, data, "text/markdown")
        except DriveError:
            return drive.update_media(target, data, "text/plain")
    try:
        return drive.upload(name, parent_id, data, "text/markdown", convert_to=GDOC)
    except DriveError:
        return drive.upload(name, parent_id, data, "text/plain", convert_to=GDOC)


def _link(file_id):
    return f"https://drive.google.com/file/d/{file_id}/view"


# ---- hub -----------------------------------------------------------------------------------------------------------

def setup_hub(drive, registry, my_drive):
    me = drive.about()["user"]["emailAddress"]
    print(f"signed in as {me}")
    hub = registry.setdefault("hub", {})
    root_id, drive_id = _root(drive, HUB_TITLE, "published", my_drive)
    hub.update(published_root=root_id, published_drive=drive_id, title=HUB_TITLE)
    hub["releases"] = drive.create_folder("releases", root_id)["id"]
    index = _json_file(drive, root_id, "index.json", {"packages": list(registry.get("packages_index", []))},
                       hub.get("index_json"))
    hub["index_json"] = index["id"]
    refresh_start_here(drive, registry)
    print(f"Skills Hub — Published: root {root_id} · releases/ {hub['releases']} · index.json {hub['index_json']} · "
          f"START HERE {hub.get('start_here')}")


def hub_start_here_text(registry):
    hub = registry["hub"]
    text = (REPO / "docs" / "start-here.md").read_text(encoding="utf-8")
    # The first paragraph of the source explains the file to maintainers; the Doc is for users.
    paragraphs = text.split("\n\n")
    text = "\n\n".join(p for p in paragraphs if not p.startswith("Source for the START HERE"))
    text = text.replace("<SKILLS_HUB_CURRENT_JSON_ID>", hub.get("current_json") or "<not released yet>")
    text = text.replace("<INDEX_JSON_ID>", hub.get("index_json") or "<not created yet>")
    packages = registry.get("packages", {})
    if packages:
        rows = "\n".join(
            f"- `{slug}` ({p.get('title', slug)}; maintainers {', '.join(p.get('maintainers', [])) or '?'}): "
            f"current.json file ID `{p.get('current_json') or 'not released yet'}`"
            + (f"; feedback/ folder ID `{p['submissions']['feedback']}`; inbox/ folder ID `{p['submissions']['inbox']}`"
               if p.get("submissions") else "")
            + ("  ← the foundation: install this one first" if p.get("foundation") else "")
            for slug, p in sorted(packages.items()))
        text += f"\n\n## Packages on this hub\n\n{rows}\n"
    return text


def package_start_here_text(registry, slug):
    p = registry["packages"][slug]
    hub = registry.get("hub", {})
    return (f"# START HERE: {p.get('title', slug)}\n\n"
            f"This is the `{slug}` package of Skills Hub, maintained by {', '.join(p.get('maintainers', [])) or 'its maintainers'}.\n\n"
            f"- Its `current.json` file ID is `{p.get('current_json') or 'not released yet'}`; releases are in `releases/`.\n"
            f"- To install it, follow the Skills Hub START HERE doc"
            + (f" ({_link(hub['start_here'])})" if hub.get("start_here") else "") +
            f" and name this package. Later updates: the `sync` skill.\n"
            f"- To contribute a skill: the `publish` skill uploads it to the inbox of the "
            f"\"{SUBMISSIONS.format(title=p.get('title', slug))}\" drive"
            + (f" (inbox folder ID `{p['submissions']['inbox']}`)" if p.get("submissions") else "") + ".\n"
            f"- To say whether a skill worked: the `feedback` skill writes one file into that drive's `feedback/`"
            + (f" (folder ID `{p['submissions']['feedback']}`)" if p.get("submissions") else "") + ".\n")


def refresh_start_here(drive, registry):
    hub = registry.get("hub", {})
    if hub.get("published_root"):
        doc = _doc(drive, hub["published_root"], "START HERE", hub_start_here_text(registry), hub.get("start_here"))
        hub["start_here"] = doc["id"]
    for slug, p in registry.get("packages", {}).items():
        if p.get("published_root"):
            doc = _doc(drive, p["published_root"], "START HERE", package_start_here_text(registry, slug), p.get("start_here"))
            p["start_here"] = doc["id"]


# ---- package -------------------------------------------------------------------------------------------------------

def setup_package(drive, registry, package_dir, my_drive):
    meta = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    slug, title = meta["package"], meta.get("title") or meta["package"]
    hub = registry.get("hub", {})
    if not hub.get("index_json"):
        raise DriveError("set up the hub first: setup_drive.py hub")
    p = registry.setdefault("packages", {}).setdefault(slug, {})
    p.update(title=title, maintainers=meta.get("maintainers", []))
    if meta.get("foundation") or slug.endswith("-foundation"):
        p["foundation"] = True
    pub_root, pub_drive = _root(drive, title, "published", my_drive)
    p.update(published_root=pub_root, published_drive=pub_drive)
    p["releases"] = drive.create_folder("releases", pub_root)["id"]
    sub_root, sub_drive = _root(drive, title, "submissions", my_drive)
    p["submissions"] = {"root": sub_root, "drive": sub_drive}
    for name in SUBMISSION_FOLDERS:
        p["submissions"][name] = drive.create_folder(name, sub_root)["id"]
    update_index(drive, registry)
    refresh_start_here(drive, registry)
    print(f"{title}: Published root {pub_root} (releases/ {p['releases']}, START HERE {p['start_here']}) · "
          f"Submissions root {sub_root} ({', '.join(f'{n}/ {p['submissions'][n]}' for n in SUBMISSION_FOLDERS)})")


def update_index(drive, registry):
    """index.json on the Skills Hub drive: slug, title, maintainers, current.json file ID per package."""
    hub = registry["hub"]
    packages = [{"slug": slug, "title": p.get("title", slug), "maintainers": p.get("maintainers", []),
                 "current_file_id": p.get("current_json"), "foundation": bool(p.get("foundation")),
                 "published_root_id": p.get("published_root"), "start_here_id": p.get("start_here")}
                for slug, p in sorted(registry.get("packages", {}).items())]
    index = _json_file(drive, hub["published_root"], "index.json", {"packages": packages}, hub.get("index_json"))
    hub["index_json"] = index["id"]
    return index


# ---- share / show --------------------------------------------------------------------------------------------------

def do_share(drive, registry, args):
    if args.hub:
        target = registry["hub"]["published_drive"] or registry["hub"]["published_root"]
        label = "Skills Hub — Published"
    else:
        p = registry["packages"][args.slug]
        if args.submissions:
            target, label = p["submissions"]["drive"] or p["submissions"]["root"], f"{p['title']} — Submissions"
        else:
            target, label = p["published_drive"] or p["published_root"], f"{p['title']} — Published"
    is_shared_drive = target == (registry["hub"].get("published_drive") if args.hub else
                                 (p["submissions"]["drive"] if args.submissions else p["published_drive"]))
    if args.domain and is_shared_drive:
        raise DriveError("a Shared Drive cannot be shared with a whole domain: add members with --user (one per "
                         "person, or a Google Group's address, which is how 'everyone in the org' is done)")
    perm = drive.share(target, args.role, email=args.user, domain=args.domain, notify=args.notify)
    print(f"{label}: {perm.get('type')} {perm.get('emailAddress') or perm.get('domain')} = {perm['role']}")


def show(drive, registry):
    print(f"account: {registry.get('account')}  (Drive says: {drive.about()['user']['emailAddress']})")
    hub = registry.get("hub", {})
    print("hub:", json.dumps(hub, indent=2))
    for slug, p in registry.get("packages", {}).items():
        print(f"package {slug}:", json.dumps(p, indent=2))
    if hub.get("index_json"):
        print("index.json on Drive:", drive.download(hub["index_json"]).decode("utf-8"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
