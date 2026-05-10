from __future__ import annotations

import json
from pathlib import Path

import pytest

from search import SearchEngine, SearchError


def _write_index(path: Path) -> None:
    payload = {
        "metadata": {"total_pages": 2, "total_terms": 3, "total_tokens": 6},
        "index": {
            "good": {
                "https://example.com/a": {"frequency": 2, "positions": [0, 2]},
                "https://example.com/b": {"frequency": 1, "positions": [1]},
            },
            "friends": {
                "https://example.com/a": {"frequency": 1, "positions": [3]},
            },
            "hello": {
                "https://example.com/b": {"frequency": 1, "positions": [0]},
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_from_file_loads_index(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    _write_index(p)

    engine = SearchEngine.from_file(p)
    assert engine.metadata["total_pages"] == 2
    assert "good" in engine.index


def test_print_term_normalizes_case(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    _write_index(p)
    engine = SearchEngine.from_file(p)

    postings = engine.print_term("GOOD")
    assert "https://example.com/a" in postings


def test_print_term_rejects_multiple_words(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    _write_index(p)
    engine = SearchEngine.from_file(p)

    with pytest.raises(SearchError):
        engine.print_term("good friends")


def test_find_returns_intersection_ranked(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    _write_index(p)
    engine = SearchEngine.from_file(p)

    # Only page a has both good and friends.
    assert engine.find("good friends") == ["https://example.com/a"]


def test_find_empty_query_raises(tmp_path: Path) -> None:
    p = tmp_path / "index.json"
    _write_index(p)
    engine = SearchEngine.from_file(p)

    with pytest.raises(SearchError):
        engine.find("$$$")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SearchError):
        SearchEngine.from_file(tmp_path / "not_exists.json")

