"""CLI entry point for the coursework search tool."""

from __future__ import annotations

import argparse
import shlex
import sys
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
    indexer = InvertedIndexer()
    crawled_pages = 0

    def _progress(page_count: int, current_url: str, pending_count: int) -> None:
        if args.verbose:
            print(
                f"[crawl] page={page_count} pending={pending_count} url={current_url}",
                flush=True,
            )

    try:
        with crawl_output_file.open("w", encoding="utf-8") as handle:
            for page in crawler.iter_crawl_pages(
                max_pages=args.max_pages,
                progress_callback=_progress,
            ):
                crawled_pages += 1
                handle.write(f"URL: {page.url}\n")
                handle.write(page.text)
                handle.write("\n\n" + ("-" * 80) + "\n\n")

                # Build the index incrementally while crawling.
                indexer.add_page(page)
    finally:
        crawler.close()

    indexer.save(index_output_file)

    print(f"Crawled pages: {crawled_pages}")
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
    parser.add_argument(
        "--mode",
        choices=["once", "shell"],
        default=None,
        help="Execution mode: once (run one command), shell (interactive REPL).",
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
    build.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-page crawl progress during build.",
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


def execute_args(args: argparse.Namespace) -> int:
    try:
        return args.func(args)
    except SearchError as exc:
        print(f"Error: {exc}")
        return 1


def run_interactive_shell() -> int:
    parser = create_parser()
    print("Interactive shell started. Type 'help' for usage, 'exit' to quit.")

    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            continue

        if not raw:
            continue

        lowered = raw.lower()
        if lowered in {"exit", "quit"}:
            return 0
        if lowered == "help":
            parser.print_help()
            continue

        try:
            tokens = shlex.split(raw)
        except ValueError as exc:
            print(f"Error: {exc}")
            continue

        if not tokens:
            continue

        # In interactive mode, build should show crawl progress by default.
        if tokens and tokens[0] == "build" and "--verbose" not in tokens:
            tokens.append("--verbose")

        try:
            args = parser.parse_args(tokens)
        except SystemExit:
            # argparse already printed the error/help.
            continue

        execute_args(args)


def main() -> int:
    if len(sys.argv) == 1:
        return run_interactive_shell()

    parser = create_parser()
    args = parser.parse_args()

    if args.mode == "shell":
        return run_interactive_shell()

    return execute_args(args)


if __name__ == "__main__":
    raise SystemExit(main())
