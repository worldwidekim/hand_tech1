"""
Download PDF files from a Google Drive folder with incremental sync.
Auth methods:
1) GOOGLE_SERVICE_ACCOUNT_JSON (raw JSON string)
2) GOOGLE_SERVICE_ACCOUNT_FILE (path to json key file)
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MANIFEST_NAME = ".sync_manifest.json"


def _load_credentials() -> service_account.Credentials:
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()

    if raw_json:
        info = json.loads(raw_json)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    if file_path:
        return service_account.Credentials.from_service_account_file(file_path, scopes=SCOPES)

    raise RuntimeError(
        "Google 인증 정보가 없습니다. GOOGLE_SERVICE_ACCOUNT_JSON 또는 GOOGLE_SERVICE_ACCOUNT_FILE을 설정하세요."
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _list_pdf_files(service: Any, folder_id: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page_token = None

    query = (
        f"'{folder_id}' in parents and trashed=false "
        "and mimeType='application/pdf'"
    )

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, modifiedTime, size)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def _download_file(service: Any, file_id: str, target_path: Path) -> None:
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with target_path.open("wb") as out:
        downloader = MediaIoBaseDownload(out, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def main() -> None:
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if not folder_id:
        raise SystemExit("GOOGLE_DRIVE_FOLDER_ID가 비어 있습니다.")

    target_dir = Path(os.getenv("RAW_PDF_DIR", "./data/raw_pdfs"))
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = target_dir / MANIFEST_NAME

    creds = _load_credentials()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    remote_files = _list_pdf_files(service, folder_id)
    manifest = _load_manifest(manifest_path)

    downloaded = 0
    skipped = 0
    seen_ids: set[str] = set()
    next_manifest: dict[str, Any] = {}

    for rf in remote_files:
        file_id = rf["id"]
        name = rf["name"]
        modified = rf.get("modifiedTime")
        safe_name = name.replace("/", "_")
        local_path = target_dir / safe_name

        seen_ids.add(file_id)
        old = manifest.get(file_id)

        needs_download = True
        if old and old.get("modifiedTime") == modified and local_path.exists():
            needs_download = False

        if needs_download:
            _download_file(service, file_id, local_path)
            downloaded += 1
            print(f"[DOWNLOADED] {safe_name}")
        else:
            skipped += 1
            print(f"[SKIPPED] {safe_name}")

        next_manifest[file_id] = {
            "name": safe_name,
            "modifiedTime": modified,
            "size": rf.get("size"),
        }

    # Remove local files no longer present in drive manifest.
    removed = 0
    for old_id, meta in manifest.items():
        if old_id not in seen_ids:
            old_file = target_dir / meta.get("name", "")
            if old_file.exists() and old_file.is_file():
                old_file.unlink()
                removed += 1
                print(f"[REMOVED] {old_file.name}")

    _save_manifest(manifest_path, next_manifest)

    print("\n=== Sync Summary ===")
    print(f"Remote PDFs: {len(remote_files)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Removed: {removed}")
    print(f"Target dir: {target_dir.resolve()}")


if __name__ == "__main__":
    main()
