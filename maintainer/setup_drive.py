#!/usr/bin/env python3
"""Create and maintain the Drive side of Skills Hub: one Shared Drive, its folders, the START HERE docs and
index.json (design.md "Drive layout"). Idempotent: every command reuses what already exists by name.

One drive, named "Skills Hub". The framework lives at its root; each package is a folder under packages/.

Usage:
  setup_drive.py hub      --account EMAIL [--my-drive]   "Skills Hub": releases/, packages/, index.json, START HERE
  setup_drive.py package  --package DIR   [--my-drive]   packages/<slug>/ (releases/, START HERE) and
                                                          packages/<slug>/submissions/ (inbox/ accepted/ rejected/ feedback/);
                                                          registers the package in index.json
  setup_drive.py nest                                      move packages that still have their own drives into packages/
  setup_drive.py start-here                                rewrite every START HERE doc with the current file IDs
  setup_drive.py share    (--hub | --package SLUG) (--domain D | --user EMAIL) --role ROLE [--submissions]
                                                          reader for users; organizer for a maintainer
  setup_drive.py show                                      what the registry knows, and what Drive says

What it records: ~/.config/skills-hub/drives.json (names and IDs; no credentials). --my-drive puts one folder in the
account's My Drive instead of a Shared Drive (for an account that may not create Shared Drives, or a test).
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[0]
sys.path.insert(0, str(HERE))
from drive import GDOC, Drive, DriveError, load_registry, save_registry  # noqa: E402

HUB_TITLE = "Skills Hub"
LEGACY_HUB_NAME = "Skills Hub — Published"
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
    sub.add_parser("nest")
    sub.add_parser("start-here")
    share = sub.add_parser("share")
    who = share.add_mutually_exclusive_group(required=True)
    who.add_argument("--hub", action="store_true")
    who.add_argument("--package", dest="slug")
    to = share.add_mutually_exclusive_group(required=True)
    to.add_argument("--domain")
    to.add_argument("--user")
    share.add_argument("--role", required=True, choices=("reader", "commenter", "writer", "fileOrganizer", "organizer"))
    share.add_argument("--submissions", action="store_true", help="the package's submissions/ folder")
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
        elif args.cmd == "nest":
            nest(drive, registry)
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

def _hub_root(drive, hub, my_drive):
    """The one Skills Hub drive (or My Drive folder). Reuses the registry, then a drive already named Skills Hub.
    Returns (root_id, drive_id); drive_id is None for a My Drive folder."""
    if hub.get("published_drive"):
        drive.rename_drive(hub["published_drive"], HUB_TITLE)
        return hub.get("published_root") or hub["published_drive"], hub["published_drive"]
    if my_drive:
        if hub.get("published_root"):
            return hub["published_root"], None
        folder = drive.create_folder(HUB_TITLE, "root")
        return folder["id"], None
    for name in (HUB_TITLE, LEGACY_HUB_NAME):
        for d in drive.list_drives():
            if d["name"] == name:
                if d["name"] != HUB_TITLE:
                    drive.rename_drive(d["id"], HUB_TITLE)
                return d["id"], d["id"]
    created = drive.create_drive(HUB_TITLE)
    return created["id"], created["id"]


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


def _move_children(drive, from_parent, to_parent):
    for child in list(drive.children(from_parent)):
        drive.move(child["id"], from_parent, to_parent)
        print(f"  moved {child['name']} -> {to_parent}")


def _delete_drive_if_empty(drive, drive_id):
    if not drive_id:
        return
    # Drive still reports children for a few seconds after the last file has moved.
    for attempt in range(4):
        left = drive.children(drive_id)
        if left:
            names = ", ".join(f["name"] for f in left)
            print(f"warning: shared drive {drive_id} still has {names}; left in place")
            return
        try:
            drive.delete_drive(drive_id)
        except DriveError as exc:
            if "cannotDeleteResourceWithChildren" in str(exc) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            print(f"warning: could not remove shared drive {drive_id}: {exc}")
            return
        print(f"removed empty shared drive {drive_id}")
        return


# ---- hub -----------------------------------------------------------------------------------------------------------

def setup_hub(drive, registry, my_drive):
    me = drive.about()["user"]["emailAddress"]
    print(f"signed in as {me}")
    hub = registry.setdefault("hub", {})
    root_id, drive_id = _hub_root(drive, hub, my_drive)
    hub.update(published_root=root_id, published_drive=drive_id, title=HUB_TITLE)
    hub["releases"] = drive.create_folder("releases", root_id)["id"]
    hub["packages"] = drive.create_folder("packages", root_id)["id"]
    if registry.get("packages"):
        update_index(drive, registry)
    else:
        index = _json_file(drive, root_id, "index.json", {"packages": []}, hub.get("index_json"))
        hub["index_json"] = index["id"]
    refresh_start_here(drive, registry)
    print(f"Skills Hub: root {root_id} · releases/ {hub['releases']} · packages/ {hub['packages']} · "
          f"index.json {hub['index_json']} · START HERE {hub.get('start_here')}")


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
            f"- To contribute a skill: the `publish` skill uploads it to this package's `submissions/inbox/`"
            + (f" (folder ID `{p['submissions']['inbox']}`)" if p.get("submissions") else "") + ".\n"
            f"- To say whether a skill worked: the `feedback` skill writes one file into `submissions/feedback/`"
            + (f" (folder ID `{p['submissions']['feedback']}`)" if p.get("submissions") else "") + ".\n")


def refresh_start_here(drive, registry, only_slug=None):
    """Rewrite START HERE. `only_slug` limits the package docs to that one package; the hub doc is always rewritten.
    A package release passes its slug so the releaser does not need write access to every other package."""
    hub = registry.get("hub", {})
    if hub.get("published_root"):
        doc = _doc(drive, hub["published_root"], "START HERE", hub_start_here_text(registry), hub.get("start_here"))
        hub["start_here"] = doc["id"]
    for slug, p in registry.get("packages", {}).items():
        if only_slug and slug != only_slug:
            continue
        if p.get("published_root"):
            doc = _doc(drive, p["published_root"], "START HERE", package_start_here_text(registry, slug), p.get("start_here"))
            p["start_here"] = doc["id"]


# ---- package -------------------------------------------------------------------------------------------------------

def _separate_drive(root_id, drive_id, hub_drive_id, folder_id):
    """True when this root is still its own Shared Drive, not a folder already inside the hub."""
    return bool(root_id and drive_id and drive_id != hub_drive_id and root_id != folder_id)


def ensure_package_tree(drive, registry, slug, title, maintainers, foundation=False):
    """packages/<slug>/ with releases/ and submissions/, inside the hub. Moves a package off its own drives."""
    hub = registry.get("hub", {})
    if not hub.get("published_root"):
        raise DriveError("set up the hub first: setup_drive.py hub")
    packages_dir = drive.create_folder("packages", hub["published_root"])
    hub["packages"] = packages_dir["id"]
    p = registry.setdefault("packages", {}).setdefault(slug, {})
    p.update(title=title, maintainers=maintainers)
    if foundation:
        p["foundation"] = True
    pkg_folder = drive.create_folder(slug, packages_dir["id"])
    hub_drive = hub.get("published_drive")
    if _separate_drive(p.get("published_root"), p.get("published_drive"), hub_drive, pkg_folder["id"]):
        print(f"{slug}: moving published files into packages/{slug}/")
        _move_children(drive, p["published_root"], pkg_folder["id"])
        _delete_drive_if_empty(drive, p["published_drive"])
    p["published_root"] = pkg_folder["id"]
    p["published_drive"] = hub_drive
    p["releases"] = drive.create_folder("releases", pkg_folder["id"])["id"]
    sub_folder = drive.create_folder("submissions", pkg_folder["id"])
    old_sub = p.get("submissions") or {}
    if _separate_drive(old_sub.get("root"), old_sub.get("drive"), hub_drive, sub_folder["id"]):
        print(f"{slug}: moving submissions into packages/{slug}/submissions/")
        _move_children(drive, old_sub["root"], sub_folder["id"])
        _delete_drive_if_empty(drive, old_sub["drive"])
    submissions = {"root": sub_folder["id"], "drive": None}
    for name in SUBMISSION_FOLDERS:
        submissions[name] = drive.create_folder(name, sub_folder["id"])["id"]
    # Keep folder IDs that were already recorded when the moved folder is the one we just found.
    p["submissions"] = submissions
    return p


def setup_package(drive, registry, package_dir, my_drive):
    meta = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    slug, title = meta["package"], meta.get("title") or meta["package"]
    if my_drive and not registry.get("hub", {}).get("published_root"):
        setup_hub(drive, registry, True)
    p = ensure_package_tree(drive, registry, slug, title, meta.get("maintainers", []),
                            foundation=bool(meta.get("foundation") or slug.endswith("-foundation")))
    update_index(drive, registry)
    refresh_start_here(drive, registry)
    print(f"{title}: packages/{slug}/ {p['published_root']} (releases/ {p['releases']}, START HERE {p['start_here']}) · "
          f"submissions/ {p['submissions']['root']} "
          f"({', '.join(f'{n}/ {p['submissions'][n]}' for n in SUBMISSION_FOLDERS)})")


def nest(drive, registry):
    """Fold every package that still has its own Shared Drive into packages/<slug>/ on the hub."""
    hub = registry.get("hub", {})
    if not hub.get("published_root"):
        raise DriveError("set up the hub first: setup_drive.py hub")
    if hub.get("published_drive"):
        drive.rename_drive(hub["published_drive"], HUB_TITLE)
    hub["packages"] = drive.create_folder("packages", hub["published_root"])["id"]
    for slug, p in list(registry.get("packages", {}).items()):
        ensure_package_tree(drive, registry, slug, p.get("title") or slug, p.get("maintainers", []),
                            foundation=bool(p.get("foundation")))
    update_index(drive, registry)
    refresh_start_here(drive, registry)
    print(f"Skills Hub: {len(registry.get('packages', {}))} package(s) under packages/ {hub['packages']}")


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
    hub = registry["hub"]
    on_shared_drive = bool(hub.get("published_drive"))
    if args.hub:
        target = hub.get("published_drive") or hub["published_root"]
        label = "Skills Hub"
    else:
        p = registry["packages"][args.slug]
        if args.submissions:
            target, label = p["submissions"]["root"], f"{p['title']} submissions/"
        else:
            target, label = p["published_root"], p["title"]
    if args.domain and on_shared_drive:
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
