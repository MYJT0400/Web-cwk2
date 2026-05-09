"""Index loading and query utilities for the CLI commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from indexer import TOKEN_PATTERN


Posting = dict[str, int | list[int]]
InvertedIndex = dict[str, dict[str, Posting]]


class SearchError(Exception):
    """Raised when index loading or searching fails."""


@dataclass
class LoadedIndex:
    """Container for loaded index content."""

    metadata: dict[str, int]
    index: InvertedIndex


class SearchEngine:
    """Provides load, print-term, and find-query behavior."""

    def __init__(self, loaded_index: LoadedIndex) -> None:
        self.metadata = loaded_index.metadata
        self.index = loaded_index.index

    @classmethod
    def from_file(cls, index_path: Path) -> "SearchEngine":
        if not index_path.exists():
            raise SearchError(f"Index file does not exist: {index_path}")

        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SearchError(f"Index file is not valid JSON: {index_path}") from exc

        if not isinstance(payload, dict):
            raise SearchError("Index payload must be a JSON object.")

        metadata = payload.get("metadata")
        index = payload.get("index")
        if not isinstance(metadata, dict) or not isinstance(index, dict):
            raise SearchError("Index payload must include 'metadata' and 'index' objects.")

        metadata_int: dict[str, int] = {}
        for key in ("total_pages", "total_terms", "total_tokens"):
            value = metadata.get(key)
            if not isinstance(value, int):
                raise SearchError(f"Metadata field '{key}' must be an integer.")
            metadata_int[key] = value

        return cls(LoadedIndex(metadata=metadata_int, index=index))

    def print_term(self, term: str) -> dict[str, Posting]:
        normalized = self._normalize_single_term(term)
        return self.index.get(normalized, {})

    def find(self, query: str) -> list[str]:
        terms = self._tokenize(query)
        if not terms:
            raise SearchError("Query is empty after tokenization.")

        postings_by_term = [self.index.get(term, {}) for term in terms]
        if any(not postings for postings in postings_by_term):
            return []

        candidate_pages = set(postings_by_term[0].keys())
        for postings in postings_by_term[1:]:
            candidate_pages &= set(postings.keys())

        def score(url: str) -> int:
            total = 0
            for postings in postings_by_term:
                total += int(postings[url]["frequency"])
            return total

        ranked = sorted(candidate_pages, key=lambda url: (-score(url), url))
        return ranked

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]

    def _normalize_single_term(self, term: str) -> str:
        tokens = self._tokenize(term)
        if not tokens:
            raise SearchError("Word is empty after tokenization.")
        if len(tokens) > 1:
            raise SearchError("Print command accepts exactly one word.")
        return tokens[0]

