from __future__ import annotations

import json
from pathlib import Path

from crawler import PageData
from indexer import InvertedIndexer


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


def test_save_writes_metadata_and_index(tmp_path: Path) -> None:
    pages = [PageData(url="https://example.com/a", text="hello world")]
    indexer = InvertedIndexer()
    indexer.build(pages)

    output = tmp_path / "inverted_index.json"
    indexer.save(output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metadata"]["total_pages"] == 1
    assert "hello" in payload["index"]
    assert "world" in payload["index"]

