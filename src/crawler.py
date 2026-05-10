"""Crawler utilities for quotes.toscrape.com."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic, sleep
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import RequestException


DEFAULT_BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class PageData:
    """Represents extracted content from a crawled page."""

    url: str
    text: str


class CrawlerError(Exception):
    """Raised when crawling fails unrecoverably."""


class QuotesCrawler:
    """Simple crawler with a mandatory politeness window between requests."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        politeness_seconds: float = 6.0,
        timeout_seconds: float = 15.0,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url
        self.politeness_seconds = politeness_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._last_request_at: float | None = None
        self._session = requests.Session()

    def crawl(self, max_pages: int | None = None) -> list[PageData]:
        """
        Crawl the entire quotes site and collect text content per page.

        Args:
            max_pages: Optional limit for local testing.

        Returns:
            A list of page payloads with URL and plain text.
        """
        page_data: list[PageData] = []
        start_url = self._normalize_url(self.base_url)
        base_host = urlparse(start_url).netloc
        queue: deque[str] = deque([start_url])
        visited: set[str] = set()

        while queue:
            if max_pages is not None and len(page_data) >= max_pages:
                break

            current_url = queue.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)
            html = self._fetch_with_retry(current_url)
            soup = BeautifulSoup(html, "html.parser")

            text = self._extract_page_text(soup)
            page_data.append(PageData(url=current_url, text=text))

            for discovered in self._discover_links(soup, current_url, base_host):
                if discovered not in visited:
                    queue.append(discovered)

        return page_data

    def close(self) -> None:
        """Release network resources."""
        self._session.close()

    def _fetch_with_retry(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                self._wait_for_politeness_window()
                response = self._session.get(url, timeout=self.timeout_seconds)
                self._last_request_at = monotonic()
                self._raise_for_status(response)
                return response.text
            except (RequestException, CrawlerError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                sleep(1.0)

        raise CrawlerError(f"Failed to fetch {url!r}: {last_error}") from last_error

    def _wait_for_politeness_window(self) -> None:
        if self._last_request_at is None:
            return

        elapsed = monotonic() - self._last_request_at
        remaining = self.politeness_seconds - elapsed
        if remaining > 0:
            sleep(remaining)

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        if response.status_code >= 400:
            raise CrawlerError(
                f"Request failed with status {response.status_code} for {response.url}"
            )

    @staticmethod
    def _extract_page_text(soup: BeautifulSoup) -> str:
        # Extract visible text for all pages so author/tag pages are not empty.
        for element in soup.select("script, style, noscript"):
            element.decompose()
        return soup.get_text(separator=" ", strip=True)

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        normalized = parsed._replace(query="", fragment="", path=path)
        return urlunparse(normalized)

    def _discover_links(
        self,
        soup: BeautifulSoup,
        current_url: str,
        base_host: str,
    ) -> list[str]:
        discovered: list[str] = []
        seen_local: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            absolute = urljoin(current_url, href)
            normalized = self._normalize_url(absolute)
            parsed = urlparse(normalized)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc != base_host:
                continue
            if normalized in seen_local:
                continue
            seen_local.add(normalized)
            discovered.append(normalized)
        return discovered
