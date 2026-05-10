from __future__ import annotations

from crawler import QuotesCrawler


def test_extract_page_text_and_discover_links() -> None:
    html = """
    <html>
      <body>
        <div class="quote">
          <span class="text">"One"</span>
          <small class="author">Author A</small>
          <div class="tags">
            <a class="tag">tag1</a>
            <a class="tag">tag2</a>
          </div>
        </div>
        <a href="/author/Albert-Einstein">author</a>
        <a href="/tag/life/page/1/">tag</a>
        <li class="next"><a href="/page/2/">Next</a></li>
      </body>
    </html>
    """

    crawler = QuotesCrawler()
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")

    text = crawler._extract_page_text(soup)
    links = crawler._discover_links(
        soup=soup,
        current_url="https://quotes.toscrape.com/",
        base_host="quotes.toscrape.com",
    )

    assert "One" in text
    assert "Author A" in text
    assert "tag1" in text
    assert "tag2" in text
    assert "https://quotes.toscrape.com/page/2/" in links
    assert "https://quotes.toscrape.com/author/Albert-Einstein" in links
    assert "https://quotes.toscrape.com/tag/life/page/1/" in links


def test_discover_links_filters_external_urls() -> None:
    html = """
    <html><body>
      <a href="https://quotes.toscrape.com/page/2/">in-domain</a>
      <a href="https://example.com/">external</a>
      <a href="#fragment">fragment-only</a>
    </body></html>
    """
    crawler = QuotesCrawler()
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")

    links = crawler._discover_links(
        soup=soup,
        current_url="https://quotes.toscrape.com/",
        base_host="quotes.toscrape.com",
    )

    assert "https://quotes.toscrape.com/page/2/" in links
    assert all("example.com" not in item for item in links)
