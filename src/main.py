"""CLI entry point for the coursework search tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from crawler import QuotesCrawler


def build_command(args: argparse.Namespace) -> int:
    crawler = QuotesCrawler(
        base_url=args.base_url,
        politeness_seconds=args.politeness,
        timeout_seconds=args.timeout,
        max_retries=args.retries,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / args.output_file

    try:
        pages = crawler.crawl(max_pages=args.max_pages)
    finally:
        crawler.close()

    with output_file.open("w", encoding="utf-8") as handle:
        for page in pages:
            handle.write(f"URL: {page.url}\n")
            handle.write(page.text)
            handle.write("\n\n" + ("-" * 80) + "\n\n")

    print(f"Crawled pages: {len(pages)}")
    print(f"Saved crawl output to: {output_file}")
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
    build.set_defaults(func=build_command)

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

