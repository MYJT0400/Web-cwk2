"""Crawler utilities for quotes.toscrape.com."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic, sleep
from urllib.parse import urljoin

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
        Crawl the quotes website and collect text content per page.

        Args:
            max_pages: Optional limit for local testing.

        Returns:
            A list of page payloads with URL and plain text.
        """
        page_data: list[PageData] = []
        next_url = self.base_url
        visited: set[str] = set()

        while next_url and next_url not in visited:
            if max_pages is not None and len(page_data) >= max_pages:
                break

            visited.add(next_url)
            html = self._fetch_with_retry(next_url)
            soup = BeautifulSoup(html, "html.parser")

            text = self._extract_page_text(soup)
            page_data.append(PageData(url=next_url, text=text))

            next_url = self._get_next_page_url(soup, next_url)

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
        quote_blocks = soup.select("div.quote")
        segments: list[str] = []

        for quote in quote_blocks:
            text_node = quote.select_one("span.text")
            author_node = quote.select_one("small.author")
            tags = [tag.get_text(strip=True) for tag in quote.select("div.tags a.tag")]

            if text_node:
                segments.append(text_node.get_text(strip=True))
            if author_node:
                segments.append(author_node.get_text(strip=True))
            if tags:
                segments.append(" ".join(tags))

        return "\n".join(segments).strip()

    @staticmethod
    def _get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
        next_link = soup.select_one("li.next a")
        if not next_link:
            return None
        href = next_link.get("href")
        if not href:
            return None
        return urljoin(current_url, href)

