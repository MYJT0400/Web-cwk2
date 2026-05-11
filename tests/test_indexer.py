from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from crawler import PageData
from indexer import InvertedIndexer


def _case_dir() -> Path:
    root = Path(__file__).resolve().parent / ".test_tmp"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_build_collects_frequency_and_positions() -> None:
    pages = [
        PageData(url="https://example.com/a", text="Good good friends"),
        PageData(url="https://example.com/b", text="good friends forever"),
    ]

    indexer = InvertedIndexer()
    index = indexer.build(pages)

    assert index["good"]["https://example.com/a"]["frequency"] == 2
    assert index["good"]["https://example.com/a"]["positions"] == [0, 1]
    assert index["friends"]["https://example.com/a"]["positions"] == [2]
    assert index["good"]["https://example.com/b"]["frequency"] == 1
    assert indexer.stats.total_pages == 2
    assert indexer.stats.total_terms >= 3


def test_save_writes_metadata_and_index() -> None:
    pages = [PageData(url="https://example.com/a", text="hello world")]
    indexer = InvertedIndexer()
    indexer.build(pages)

    case_dir = _case_dir()
    output = case_dir / "inverted_index.json"
    try:
        indexer.save(output)
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["metadata"]["total_pages"] == 1
        assert "hello" in payload["index"]
        assert "world" in payload["index"]
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def test_add_page_builds_index_incrementally() -> None:
    indexer = InvertedIndexer()
    indexer.add_page(PageData(url="https://example.com/a", text="good good"))
    indexer.add_page(PageData(url="https://example.com/b", text="good friends"))

    assert indexer.stats.total_pages == 2
    assert indexer.stats.total_tokens == 4
    assert indexer.index["good"]["https://example.com/a"]["frequency"] == 2
    assert indexer.index["good"]["https://example.com/b"]["frequency"] == 1
    assert indexer.index["friends"]["https://example.com/b"]["positions"] == [1]
