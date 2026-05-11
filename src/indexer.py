"""Inverted index utilities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crawler import PageData


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


@dataclass
class IndexStats:
    """Summary information for generated index files."""

    total_pages: int
    total_terms: int
    total_tokens: int


class InvertedIndexer:
    """Builds and persists an inverted index for crawled pages."""

    def __init__(self) -> None:
        self.index: dict[str, dict[str, dict[str, int | list[int]]]] = {}
        self.stats = IndexStats(total_pages=0, total_terms=0, total_tokens=0)

    def add_page(self, page: "PageData") -> None:
        """Incrementally add one page into the existing inverted index."""
        tokens = self._tokenize(page.text)
        self.stats.total_pages += 1
        self.stats.total_tokens += len(tokens)

        for position, token in enumerate(tokens):
            postings = self.index.setdefault(token, {})
            posting = postings.setdefault(page.url, {"frequency": 0, "positions": []})
            posting["frequency"] = int(posting["frequency"]) + 1
            posting["positions"].append(position)

        self.stats.total_terms = len(self.index)

    def build(self, pages: list["PageData"]) -> dict[str, dict[str, dict[str, int | list[int]]]]:
        self.index = {}
        self.stats = IndexStats(total_pages=0, total_terms=0, total_tokens=0)
        for page in pages:
            self.add_page(page)
        return self.index

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": {
                "total_pages": self.stats.total_pages,
                "total_terms": self.stats.total_terms,
                "total_tokens": self.stats.total_tokens,
            },
            "index": self.index,
        }

        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
