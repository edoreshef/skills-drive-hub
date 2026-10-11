#!/usr/bin/env python3
"""A small Google Drive v3 client for the maintainer tools: standard library only, one bearer token.

The token comes from the maintainer's own Google sign-in, in this order:
  1. the environment variable SKILLS_HUB_DRIVE_TOKEN (an access token);
  2. `gcloud auth print-access-token --account <account>`, where the account is --account,
     the environment variable SKILLS_HUB_DRIVE_ACCOUNT, or the one saved in the registry
     (~/.config/skills-hub/drives.json). Sign in once with
     `gcloud auth login <account> --enable-gdrive-access` (the Drive scope is needed to create
     Shared Drives and upload).

Nothing here stores a credential. The registry holds names and file IDs only.

Everything that writes takes `supportsAllDrives=true`, so it works in a Shared Drive and in My Drive.
"""

import json
import mimetypes
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"
FOLDER = "application/vnd.google-apps.folder"
GDOC = "application/vnd.google-apps.document"
FILE_FIELDS = "id, name, mimeType, size, sha256Checksum, md5Checksum, modifiedTime, parents, driveId, webViewLink"
REGISTRY = Path(os.environ.get("SKILLS_HUB_REGISTRY") or Path.home() / ".config" / "skills-hub" / "drives.json")


class DriveError(RuntimeError):
    pass


# ---- registry: the drives and fixed file IDs the maintainer created ------------------------------------------------

def load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"account": None, "hub": {}, "packages": {}}


def save_registry(registry):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


# ---- auth ----------------------------------------------------------------------------------------------------------

def access_token(account=None):
    token = os.environ.get("SKILLS_HUB_DRIVE_TOKEN")
    if token:
        return token
    account = account or os.environ.get("SKILLS_HUB_DRIVE_ACCOUNT") or load_registry().get("account")
    if not account:
        raise DriveError("no Google account: pass --account, or set SKILLS_HUB_DRIVE_ACCOUNT")
    result = subprocess.run(["gcloud", "auth", "print-access-token", "--account", account],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise DriveError(f"gcloud has no live sign-in for {account}: run "
                         f"`gcloud auth login {account} --enable-gdrive-access`\n{result.stderr.strip()[:300]}")
    return result.stdout.strip()


class Drive:
    def __init__(self, account=None):
        self.account = account
        self._token = None

    # -- transport --

    def _headers(self, extra=None):
        if self._token is None:
            self._token = access_token(self.account)
        return {"Authorization": f"Bearer {self._token}", **(extra or {})}

    def request(self, method, url, params=None, body=None, headers=None, raw=False):
        params = {k: v for k, v in (params or {}).items() if v is not None}
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = body
        hdrs = dict(headers or {})
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json; charset=UTF-8")
        req = urllib.request.Request(url, method=method, data=data, headers=self._headers(hdrs))
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:600]
            raise DriveError(f"{method} {url.split('?')[0]} -> HTTP {exc.code}: {detail}") from None
        if raw:
            return payload
        return json.loads(payload) if payload else {}

    # -- read --

    def about(self):
        return self.request("GET", f"{API}/about", {"fields": "user(emailAddress,displayName)"})

    def list_files(self, q, drive_id=None, fields=FILE_FIELDS):
        params = {"q": q, "pageSize": 1000, "fields": f"nextPageToken, files({fields})",
                  "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if drive_id:
            params.update(corpora="drive", driveId=drive_id)
        out, token = [], None
        while True:
            page = self.request("GET", f"{API}/files", {**params, "pageToken": token})
            out.extend(page.get("files", []))
            token = page.get("nextPageToken")
            if not token:
                return out

    def children(self, parent_id, name=None, drive_id=None):
        q = f"'{_q(parent_id)}' in parents and trashed = false"
        if name:
            q += f" and name = '{_q(name)}'"
        return self.list_files(q, drive_id)

    def get(self, file_id, fields=FILE_FIELDS):
        return self.request("GET", f"{API}/files/{file_id}", {"fields": fields, "supportsAllDrives": "true"})

    def download(self, file_id):
        return self.request("GET", f"{API}/files/{file_id}", {"alt": "media", "supportsAllDrives": "true"}, raw=True)

    def export(self, file_id, mime="text/plain"):
        return self.request("GET", f"{API}/files/{file_id}/export", {"mimeType": mime}, raw=True)

    def list_drives(self):
        out, token = [], None
        while True:
            page = self.request("GET", f"{API}/drives", {"pageSize": 100, "pageToken": token, "fields": "nextPageToken, drives(id, name)"})
            out.extend(page.get("drives", []))
            token = page.get("nextPageToken")
            if not token:
                return out

    # -- write --

    def create_drive(self, name):
        """A Shared Drive by name; reuses one that already exists with that exact name."""
        for d in self.list_drives():
            if d["name"] == name:
                return d
        return self.request("POST", f"{API}/drives", {"requestId": str(uuid.uuid4())}, {"name": name})

    def create_folder(self, name, parent_id):
        """A folder by name directly under parent; reuses one that already exists."""
        found = [f for f in self.children(parent_id, name) if f["mimeType"] == FOLDER]
        if found:
            return found[0]
        return self.request("POST", f"{API}/files", {"supportsAllDrives": "true", "fields": FILE_FIELDS},
                            {"name": name, "mimeType": FOLDER, "parents": [parent_id]})

    def upload(self, name, parent_id, data, mime=None, convert_to=None):
        """Create a file (multipart). `convert_to` = a Google type (GDOC) to import the bytes into."""
        mime = mime or mimetypes.guess_type(name)[0] or "application/octet-stream"
        metadata = {"name": name, "parents": [parent_id]}
        if convert_to:
            metadata["mimeType"] = convert_to
        body, boundary = _multipart(metadata, data, mime)
        return self.request("POST", f"{UPLOAD}/files", {"uploadType": "multipart", "supportsAllDrives": "true",
                                                         "fields": FILE_FIELDS},
                            body, {"Content-Type": f"multipart/related; boundary={boundary}"})

    def update_media(self, file_id, data, mime="application/octet-stream"):
        """Replace a file's bytes in place: the file ID stays the same (what the connector's update_file can't do)."""
        return self.request("PATCH", f"{UPLOAD}/files/{file_id}",
                            {"uploadType": "media", "supportsAllDrives": "true", "fields": FILE_FIELDS},
                            data, {"Content-Type": mime})

    def move(self, file_id, from_parent, to_parent):
        """Move a file between folders (works inside a Shared Drive)."""
        return self.request("PATCH", f"{API}/files/{file_id}",
                            {"addParents": to_parent, "removeParents": from_parent, "supportsAllDrives": "true",
                             "fields": FILE_FIELDS}, {})

    def share(self, file_or_drive_id, role, email=None, domain=None, notify=False):
        """Permission on a file or a Shared Drive. role: reader | commenter | writer | fileOrganizer | organizer."""
        perm = {"role": role}
        if email:
            perm.update(type="user", emailAddress=email)
        elif domain:
            perm.update(type="domain", domain=domain)
        else:
            raise DriveError("share needs an email or a domain")
        return self.request("POST", f"{API}/files/{file_or_drive_id}/permissions",
                            {"supportsAllDrives": "true", "sendNotificationEmail": "true" if notify else "false",
                             "fields": "id, role, type, emailAddress, domain"}, perm)

    def permissions(self, file_or_drive_id):
        return self.request("GET", f"{API}/files/{file_or_drive_id}/permissions",
                            {"supportsAllDrives": "true", "fields": "permissions(id, role, type, emailAddress, domain)"}
                            ).get("permissions", [])


def _q(text):
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _multipart(metadata, data, mime):
    boundary = f"skills-hub-{uuid.uuid4().hex}"
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(metadata)}\r\n"
            f"--{boundary}\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode()
    return body, boundary
