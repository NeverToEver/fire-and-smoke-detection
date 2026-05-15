"""Runtime helpers for Streamlit state, uploads, and exports."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import streamlit as st

from ui import UPLOAD_DIR


@dataclass(frozen=True)
class PreparedDownload:
    """Stable payload and filename for a Streamlit download button."""

    data: bytes
    file_name: str
    mime: str


def file_fingerprint(uploaded_file) -> str:
    """Return a stable content fingerprint for a Streamlit UploadedFile."""
    return hashlib.sha256(uploaded_file.getbuffer()).hexdigest()


def stable_upload_stem(uploaded_file, prefix: str = "") -> str:
    """Build a filesystem-safe stem that changes when uploaded content changes."""
    raw_stem = Path(uploaded_file.name).stem or "upload"
    safe_stem = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in raw_stem).strip("_")
    safe_stem = safe_stem or "upload"
    digest = file_fingerprint(uploaded_file)[:12]
    name = f"{safe_stem}_{digest}"
    return f"{prefix}{name}" if prefix else name


def should_process_upload(state_key: str, uploaded_file) -> bool:
    """Record an upload fingerprint and return True only for new content."""
    fp = file_fingerprint(uploaded_file)
    if st.session_state.get(state_key) == fp:
        return False
    st.session_state[state_key] = fp
    return True


def reset_upload_fingerprint(state_key: str) -> None:
    st.session_state.pop(state_key, None)


def _assert_safe_zip_member(member: str, target_root: Path) -> None:
    member_path = (target_root / member).resolve()
    safe_root = target_root.resolve()
    try:
        member_path.relative_to(safe_root)
    except ValueError as exc:
        raise ValueError(f"压缩包包含非法路径: {member}") from exc


def safe_extract_zip(uploaded_zip, subdir: str, prefix: str = "") -> Path:
    """
    Safely extract an uploaded zip into .streamlit_uploads.

    The destination includes the uploaded file content fingerprint, so dragging a
    changed zip with the same filename creates a fresh extraction directory.
    """
    extract_dir = UPLOAD_DIR / subdir / stable_upload_stem(uploaded_zip, prefix=prefix)
    if extract_dir.exists():
        return extract_dir.resolve()

    tmp_dir = extract_dir.with_name(f".tmp_{extract_dir.name}")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=False)

    try:
        safe_root = tmp_dir.resolve()
        with zipfile.ZipFile(io.BytesIO(uploaded_zip.getbuffer())) as zf:
            for info in zf.infolist():
                _assert_safe_zip_member(info.filename, safe_root)
            zf.extractall(tmp_dir)
        os.replace(tmp_dir, extract_dir)
    except Exception:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        raise

    return extract_dir.resolve()


def reset_keys(*keys: str) -> None:
    for key in keys:
        st.session_state.pop(key, None)


def reset_state_on_change(signature_key: str, signature: str, keys_to_clear: Iterable[str]) -> bool:
    """Clear stale session keys when a page input signature changes."""
    if st.session_state.get(signature_key) == signature:
        return False
    reset_keys(*keys_to_clear)
    st.session_state[signature_key] = signature
    return True


def export_timestamp(state_key: str) -> str:
    """Return a stable timestamp for a rendered result block."""
    if state_key not in st.session_state:
        st.session_state[state_key] = datetime.now().strftime("%Y%m%d_%H%M%S")
    return st.session_state[state_key]


def clear_export_timestamp(state_key: str) -> None:
    st.session_state.pop(state_key, None)


def json_download(payload: dict[str, Any], file_name: str) -> PreparedDownload:
    data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    return PreparedDownload(data=data, file_name=file_name, mime="application/json")


def bytesio_download(buf: io.BytesIO, file_name: str, mime: str) -> PreparedDownload:
    return PreparedDownload(data=buf.getvalue(), file_name=file_name, mime=mime)
