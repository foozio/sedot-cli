from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .utils import build_filename


DEFAULT_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "accept-language": "en-US,en;q=0.9",
}


class ScrapeError(RuntimeError):
    """Raised when the video metadata cannot be retrieved."""


@dataclass
class VideoMetadata:
    platform: str
    source_url: str
    video_url: str
    filename: str
    title: str | None = None
    caption: str | None = None


class BaseScraper:
    platform: str = "generic"
    domains: Iterable[str] = ()

    def __init__(self, session: requests.Session):
        self.session = session

    def can_handle(self, url: str) -> bool:
        hostname = urlparse(url).netloc.lower()
        return any(
            hostname == domain or hostname.endswith(f".{domain}") for domain in self.domains
        )

    def scrape(self, url: str) -> VideoMetadata:
        raise NotImplementedError

    def _fetch_html(self, url: str) -> str:
        response = self.session.get(url, headers=DEFAULT_HEADERS, timeout=20)
        response.raise_for_status()
        return response.text

    def _extract_video_metadata(self, html: str, source_url: str) -> VideoMetadata:
        soup = BeautifulSoup(html, "html.parser")
        video_url = self._extract_video_url(soup)
        if not video_url:
            raise ScrapeError("Unable to locate video URL in the page metadata.")

        title = self._get_meta_content(soup, "og:title")
        caption = self._get_meta_content(soup, "og:description")
        filename = build_filename(title, source_url, self.platform)
        return VideoMetadata(
            platform=self.platform,
            source_url=source_url,
            video_url=video_url,
            filename=filename,
            title=title,
            caption=caption,
        )

    @staticmethod
    def _get_meta_content(soup: BeautifulSoup, attribute: str) -> str | None:
        tag = soup.find("meta", attrs={"property": attribute}) or soup.find(
            "meta", attrs={"name": attribute}
        )
        content = (tag.get("content") or "").strip() if tag else None
        return content or None

    def _extract_video_url(self, soup: BeautifulSoup) -> str | None:
        for prop in ("og:video:secure_url", "og:video:url", "og:video"):
            tag = soup.find("meta", attrs={"property": prop})
            if tag and tag.get("content"):
                return (tag.get("content") or "").strip()
        return self._extract_from_json_ld(soup)

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> str | None:
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue
            video_url = self._walk_json_for_video(data)
            if video_url:
                return video_url
        return None

    def _walk_json_for_video(self, data) -> str | None:
        if isinstance(data, dict):
            if data.get("contentUrl"):
                return str(data["contentUrl"])
            if data.get("video"):
                return self._walk_json_for_video(data["video"])
            for value in data.values():
                candidate = self._walk_json_for_video(value)
                if candidate:
                    return candidate
        elif isinstance(data, list):
            for item in data:
                candidate = self._walk_json_for_video(item)
                if candidate:
                    return candidate
        return None


class InstagramScraper(BaseScraper):
    platform = "instagram"
    domains = ("instagram.com",)

    def scrape(self, url: str) -> VideoMetadata:
        html = self._fetch_html(url)
        return self._extract_video_metadata(html, url)


class ThreadsScraper(BaseScraper):
    platform = "threads"
    domains = ("threads.net", "threads.com", "www.threads.com")

    def scrape(self, url: str) -> VideoMetadata:
        html = self._fetch_html(url)
        return self._extract_video_metadata(html, url)
