"""CLI entry point for the coursework search tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from crawler import QuotesCrawler
from indexer import InvertedIndexer
from search import SearchEngine, SearchError


def build_command(args: argparse.Namespace) -> int:
    crawler = QuotesCrawler(
        base_url=args.base_url,
        politeness_seconds=args.politeness,
        timeout_seconds=args.timeout,
        max_retries=args.retries,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    crawl_output_file = output_dir / args.output_file
    index_output_file = output_dir / args.index_file

    try:
        pages = crawler.crawl(max_pages=args.max_pages)
    finally:
        crawler.close()

    with crawl_output_file.open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(f"URL: {page.url}\n")
            handle.write(page.text)
            handle.write("\n\n" + ("-" * 80) + "\n\n")

    indexer = InvertedIndexer()
    indexer.build(pages)
    indexer.save(index_output_file)

    print(f"Crawled pages: {len(pages)}")
    print(f"Saved crawl output to: {crawl_output_file}")
    print(f"Saved inverted index to: {index_output_file}")
    print(
        "Index summary: "
        f"{indexer.stats.total_terms} terms, "
        f"{indexer.stats.total_tokens} tokens"
    )
    return 0


def load_command(args: argparse.Namespace) -> int:
    index_path = Path(args.index_path)
    engine = SearchEngine.from_file(index_path)
    print(f"Loaded index from: {index_path}")
    print(
        "Index summary: "
        f"{engine.metadata['total_pages']} pages, "
        f"{engine.metadata['total_terms']} terms, "
        f"{engine.metadata['total_tokens']} tokens"
    )
    return 0


def print_command(args: argparse.Namespace) -> int:
    engine = SearchEngine.from_file(Path(args.index_path))
    postings = engine.print_term(args.word)
    if not postings:
        print(f"No entries found for word: {args.word!r}")
        return 0

    print(f"Word: {args.word!r}")
    for url, stats in sorted(postings.items()):
        frequency = int(stats["frequency"])
        positions = stats["positions"]
        print(f"- {url}")
        print(f"  frequency={frequency}")
        print(f"  positions={positions}")
    return 0


def find_command(args: argparse.Namespace) -> int:
    engine = SearchEngine.from_file(Path(args.index_path))
    query = " ".join(args.query_terms)
    urls = engine.find(query)
    if not urls:
        print(f"No pages found for query: {query!r}")
        return 0

    print(f"Query: {query!r}")
    print("Matched pages:")
    for idx, url in enumerate(urls, start=1):
        print(f"{idx}. {url}")
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search_tool",
        description="Coursework 2 search tool CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Crawl website and prepare data.")
    build.add_argument(
        "--base-url",
        default="https://quotes.toscrape.com/",
        help="Start URL for crawler.",
    )
    build.add_argument(
        "--politeness",
        type=float,
        default=6.0,
        help="Delay in seconds between HTTP requests.",
    )
    build.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds.",
    )
    build.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries for failed HTTP requests.",
    )
    build.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit for local testing.",
    )
    build.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for crawl artifacts.",
    )
    build.add_argument(
        "--output-file",
        default="crawl_pages.txt",
        help="Raw crawl output filename.",
    )
    build.add_argument(
        "--index-file",
        default="inverted_index.json",
        help="Output filename for compiled inverted index.",
    )
    build.set_defaults(func=build_command)

    load = subparsers.add_parser("load", help="Load index file and show summary.")
    load.add_argument(
        "--index-path",
        default="data/inverted_index.json",
        help="Path to compiled inverted index file.",
    )
    load.set_defaults(func=load_command)

    print_term = subparsers.add_parser(
        "print", help="Print postings for one word from the loaded index file."
    )
    print_term.add_argument("word", help="Single word to inspect in index.")
    print_term.add_argument(
        "--index-path",
        default="data/inverted_index.json",
        help="Path to compiled inverted index file.",
    )
    print_term.set_defaults(func=print_command)

    find = subparsers.add_parser("find", help="Find pages that contain query terms.")
    find.add_argument(
        "query_terms",
        nargs="+",
        help="Search query terms. Example: find good friends",
    )
    find.add_argument(
        "--index-path",
        default="data/inverted_index.json",
        help="Path to compiled inverted index file.",
    )
    find.set_defaults(func=find_command)

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except SearchError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
