"""
Media storage helpers (local filesystem).
"""

from __future__ import annotations

import os
import uuid
from typing import Tuple
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

    os.makedirs(os.path.join(media_root, folder), exist_ok=True)

    original_name = secure_filename(file_storage.filename or "upload")
    _, ext = os.path.splitext(original_name)
    ext = ext or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = f"{folder}/{filename}"
    full_path = os.path.join(media_root, relative_path)

    file_storage.save(full_path)

    absolute_url = f"{base_url}{media_url}/{relative_path}"
    return absolute_url, relative_path
