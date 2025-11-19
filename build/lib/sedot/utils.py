from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


def slugify(value: str, fallback: str = "video") -> str:
    """Create a filesystem-friendly slug from a string."""
    if not value:
        return fallback
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def filename_from_url(url: str) -> str:
    """Return last meaningful part of a URL to help with filenames."""
    parsed = urlparse(url)
    candidate = Path(parsed.path).name or parsed.netloc
    candidate = candidate.strip("/")
    return candidate or "download"


def ensure_extension(name: str, extension: str = ".mp4") -> str:
    """Ensure a filename ends with the desired extension."""
    if not name.lower().endswith(extension):
        return f"{name}{extension}"
    return name


def build_filename(title: str | None, source_url: str, platform: str) -> str:
    """Create a descriptive filename for the downloaded asset."""
    base_parts = [
        slugify(platform, platform),
        slugify(filename_from_url(source_url)),
    ]
    if title:
        base_parts.insert(1, slugify(title))
    base = "-".join(filter(None, base_parts))
    return ensure_extension(base or "sedot-video")
