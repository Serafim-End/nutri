"""
Media storage helpers (local filesystem).
"""

from __future__ import annotations

import os
import uuid
from typing import Iterable, Tuple
from werkzeug.utils import secure_filename
from flask import current_app, request


def save_image(file_storage, folder: str) -> Tuple[str, str]:
    """
    Save uploaded image to local media folder.

    Returns:
        (absolute_url, relative_path)
    """
    media_root = current_app.config.get("MEDIA_ROOT", "/app/media")
    media_url = current_app.config.get("MEDIA_URL", "/media").rstrip("/")
    base_url = current_app.config.get("MEDIA_BASE_URL") or request.host_url.rstrip("/")

    try:
        os.makedirs(os.path.join(media_root, folder), exist_ok=True)
    except OSError as exc:
        raise ValueError(f"Failed to prepare media directory: {exc}") from exc

    original_name = secure_filename(file_storage.filename or "upload")
    _, ext = os.path.splitext(original_name)
    ext = ext or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = f"{folder}/{filename}"
    full_path = os.path.join(media_root, relative_path)

    try:
        file_storage.save(full_path)
    except OSError as exc:
        raise ValueError(f"Failed to save image: {exc}") from exc

    absolute_url = f"{base_url}{media_url}/{relative_path}"
    return absolute_url, relative_path


def save_file(
    file_storage,
    folder: str,
    allowed_exts: Iterable[str] | None = None,
    max_bytes: int | None = None,
) -> Tuple[str, str, int]:
    """
    Save uploaded file to local media folder with basic validation.

    Returns:
        (absolute_url, relative_path, file_size_bytes)
    """
    media_root = current_app.config.get("MEDIA_ROOT", "/app/media")
    media_url = current_app.config.get("MEDIA_URL", "/media").rstrip("/")
    base_url = current_app.config.get("MEDIA_BASE_URL") or request.host_url.rstrip("/")

    try:
        os.makedirs(os.path.join(media_root, folder), exist_ok=True)
    except OSError as exc:
        raise ValueError(f"Failed to prepare media directory: {exc}") from exc

    original_name = secure_filename(file_storage.filename or "upload")
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()

    if allowed_exts is not None and ext not in allowed_exts:
        raise ValueError("Unsupported file type")

    if not ext:
        ext = ".bin"

    filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = f"{folder}/{filename}"
    full_path = os.path.join(media_root, relative_path)

    try:
        file_storage.save(full_path)
    except OSError as exc:
        raise ValueError(f"Failed to save file: {exc}") from exc

    try:
        file_size = os.path.getsize(full_path)
    except OSError as exc:
        raise ValueError(f"Failed to stat saved file: {exc}") from exc

    if max_bytes is not None and file_size > max_bytes:
        try:
            os.remove(full_path)
        except OSError:
            pass
        raise ValueError("File too large")

    absolute_url = f"{base_url}{media_url}/{relative_path}"
    return absolute_url, relative_path, file_size
