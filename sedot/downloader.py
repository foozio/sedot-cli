from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .fetchers import (
    DEFAULT_HEADERS,
    BaseScraper,
    InstagramScraper,
    ScrapeError,
    ThreadsScraper,
    VideoMetadata,
)


@dataclass
class DownloadResult:
    metadata: VideoMetadata
    output_path: Path


class VideoDownloader:
    """High level interface to resolve metadata and download files."""

    def __init__(self, session: requests.Session | None = None, scrapers: Iterable[BaseScraper] | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if scrapers is None:
            scrapers = (
                InstagramScraper(self.session),
                ThreadsScraper(self.session),
            )
        self.scrapers = tuple(scrapers)

    def fetch_metadata(self, raw_url: str) -> VideoMetadata:
        url = self._normalize_url(raw_url)
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return scraper.scrape(url)
        raise ScrapeError(
            f"sedot does not support the domain in '{raw_url}'. "
            "Pass a full Instagram or Threads post URL."
        )

    def download(self, metadata: VideoMetadata, output_dir: Path, overwrite: bool = False) -> DownloadResult:
        destination_dir = Path(output_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        file_path = destination_dir / metadata.filename
        if file_path.exists() and not overwrite:
            raise FileExistsError(
                f"{file_path} already exists. Use --overwrite to replace it."
            )

        response = self.session.get(metadata.video_url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))

        columns = (
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )
        progress = Progress(*columns, transient=True)
        task_id: TaskID | None = None

        with progress:
            task_id = progress.add_task("downloading", total=total if total > 0 else None)
            with open(file_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    if task_id is not None:
                        progress.advance(task_id, len(chunk))

        return DownloadResult(metadata=metadata, output_path=file_path)

    @staticmethod
    def _normalize_url(url: str) -> str:
        candidate = url.strip()
        if not candidate:
            raise ScrapeError("Empty URL provided.")
        parsed = urlparse(candidate)
        if not parsed.scheme:
            candidate = f"https://{candidate}"
        return candidate
