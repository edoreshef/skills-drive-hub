#!/usr/bin/env python3
"""A stand-in for the claude.ai Google Drive connector, as a local stdio MCP server (standard library only).

Same tool names and result shapes as the connector (spikes/README.md S1, S2): `search_files`, `get_file_metadata`,
`read_file_content` (a text rendering), `download_file_content` ({content: base64, id, mimeType, title}),
`create_file`. Read-mostly: `create_file` is the one write, as in the connector. Auth is the maintainer's gcloud
sign-in through maintainer/drive.py, so this is for end-to-end tests of START HERE and sync on a host without the
real connector (headless Claude Code, Cursor), not for users.

Run (Claude Code):  claude -p --mcp-config spikes/drive-mcp/mcp.json --strict-mcp-config ...
"""

import base64
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "maintainer"))
from drive import API, GDOC, Drive, DriveError  # noqa: E402

drive = Drive()

TOOLS = [
    {"name": "search_files",
     "description": "Search Google Drive. Query syntax: title contains 'x', parentId = '<folder id>', fullText contains 'x', "
                    "mimeType = 'x', combined with and/or/not. Returns files with id, title, mimeType, modifiedTime and a "
                    "nextPageToken when there are more.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "pageToken": {"type": "string"},
                                                      "pageSize": {"type": "integer"},
                                                      "excludeContentSnippets": {"type": "boolean"}},
                     "required": ["query"]}},
    {"name": "get_file_metadata",
     "description": "Metadata of one file by ID: title, mimeType, size, modifiedTime, parents, webViewLink.",
     "inputSchema": {"type": "object", "properties": {"fileId": {"type": "string"}}, "required": ["fileId"]}},
    {"name": "read_file_content",
     "description": "Read a file as text (Google Docs are exported as text; prose only, not byte-exact).",
     "inputSchema": {"type": "object", "properties": {"fileId": {"type": "string"}}, "required": ["fileId"]}},
    {"name": "download_file_content",
     "description": "Download a file's raw bytes. Returns JSON {content: base64, id, mimeType, title}. For a Google "
                    "Sheet pass exportMimeType (e.g. the .xlsx type). Byte-exact: use this for every package file.",
     "inputSchema": {"type": "object", "properties": {"fileId": {"type": "string"}, "exportMimeType": {"type": "string"}},
                     "required": ["fileId"]}},
    {"name": "create_file",
     "description": "Create a file in a folder. Give textContent (text) or content (base64) and contentMimeType; "
                    "disableConversionToGoogleType true keeps it as uploaded.",
     "inputSchema": {"type": "object", "properties": {"title": {"type": "string"}, "parentId": {"type": "string"},
                                                      "textContent": {"type": "string"}, "content": {"type": "string"},
                                                      "contentMimeType": {"type": "string"},
                                                      "disableConversionToGoogleType": {"type": "boolean"}},
                     "required": ["title", "parentId"]}},
]


def _translate(q: str) -> str:
    """Connector syntax -> Drive API syntax."""
    import re
    q = re.sub(r"\btitle\b", "name", q)
    q = re.sub(r"parentId\s*=\s*'([^']+)'", r"'\1' in parents", q)
    if "trashed" not in q:
        q += " and trashed = false"
    return q


def _brief(f: dict) -> dict:
    return {"id": f["id"], "title": f["name"], "mimeType": f["mimeType"], "modifiedTime": f.get("modifiedTime"),
            "size": f.get("size")}


def call(name: str, a: dict):
    if name == "search_files":
        params = {"q": _translate(a["query"]), "pageSize": min(int(a.get("pageSize") or 100), 1000),
                  "fields": "nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                  "supportsAllDrives": "true", "includeItemsFromAllDrives": "true", "corpora": "allDrives",
                  "pageToken": a.get("pageToken")}
        page = drive.request("GET", f"{API}/files", params)
        out = {"files": [_brief(f) for f in page.get("files", [])]}
        if page.get("nextPageToken"):
            out["nextPageToken"] = page["nextPageToken"]
        return out
    if name == "get_file_metadata":
        f = drive.get(a["fileId"])
        return _brief(f) | {"parents": f.get("parents"), "webViewLink": f.get("webViewLink"), "driveId": f.get("driveId")}
    if name == "read_file_content":
        meta = drive.get(a["fileId"], "id, name, mimeType")
        if meta["mimeType"].startswith("application/vnd.google-apps."):
            text = drive.export(a["fileId"], "text/plain").decode("utf-8", "replace")
        else:
            text = drive.download(a["fileId"]).decode("utf-8", "replace")
        return {"title": meta["name"], "mimeType": meta["mimeType"], "text": text}
    if name == "download_file_content":
        meta = drive.get(a["fileId"], "id, name, mimeType")
        if a.get("exportMimeType"):
            data = drive.export(a["fileId"], a["exportMimeType"])
        else:
            data = drive.download(a["fileId"])
        return {"content": base64.b64encode(data).decode(), "id": meta["id"], "mimeType": meta["mimeType"], "title": meta["name"]}
    if name == "create_file":
        data = base64.b64decode(a["content"]) if a.get("content") else (a.get("textContent") or "").encode("utf-8")
        f = drive.upload(a["title"], a["parentId"], data, a.get("contentMimeType") or "text/plain",
                         convert_to=None if a.get("disableConversionToGoogleType", True) else GDOC)
        return _brief(f) | {"sha256Checksum": f.get("sha256Checksum")}
    raise ValueError(f"unknown tool {name}")


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    out["error" if error else "result"] = error if error else result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        method, msg_id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
        if method == "initialize":
            reply(msg_id, {"protocolVersion": params.get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}},
                           "serverInfo": {"name": "google_drive", "version": "0.1"}})
        elif method == "notifications/initialized" or msg_id is None:
            continue
        elif method == "ping":
            reply(msg_id, {})
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            try:
                result = call(params["name"], params.get("arguments") or {})
                reply(msg_id, {"content": [{"type": "text", "text": json.dumps(result)}]})
            except (DriveError, ValueError, KeyError) as exc:
                reply(msg_id, {"content": [{"type": "text", "text": f"Error: {exc}"}], "isError": True})
            except Exception:  # noqa: BLE001
                reply(msg_id, {"content": [{"type": "text", "text": "Error: " + traceback.format_exc()[-800:]}], "isError": True})
        else:
            reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    main()
