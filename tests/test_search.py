from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from search import SearchEngine, SearchError


def _case_dir() -> Path:
    root = Path(__file__).resolve().parent / ".test_tmp"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def test_from_file_loads_index() -> None:
    case_dir = _case_dir()
    p = case_dir / "index.json"
    try:
        _write_index(p)
        engine = SearchEngine.from_file(p)
        assert engine.metadata["total_pages"] == 2
        assert "good" in engine.index
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_print_term_normalizes_case() -> None:
    case_dir = _case_dir()
    p = case_dir / "index.json"
    try:
        _write_index(p)
        engine = SearchEngine.from_file(p)
        postings = engine.print_term("GOOD")
        assert "https://example.com/a" in postings
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_print_term_rejects_multiple_words() -> None:
    case_dir = _case_dir()
    p = case_dir / "index.json"
    try:
        _write_index(p)
        engine = SearchEngine.from_file(p)
        with pytest.raises(SearchError):
            engine.print_term("good friends")
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_find_returns_intersection_ranked() -> None:
    case_dir = _case_dir()
    p = case_dir / "index.json"
    try:
        _write_index(p)
        engine = SearchEngine.from_file(p)
        # Only page a has both good and friends.
        assert engine.find("good friends") == ["https://example.com/a"]
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_find_empty_query_raises() -> None:
    case_dir = _case_dir()
    p = case_dir / "index.json"
    try:
        _write_index(p)
        engine = SearchEngine.from_file(p)
        with pytest.raises(SearchError):
            engine.find("$$$")
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_missing_file_raises() -> None:
    case_dir = _case_dir()
    try:
        with pytest.raises(SearchError):
            SearchEngine.from_file(case_dir / "not_exists.json")
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)
