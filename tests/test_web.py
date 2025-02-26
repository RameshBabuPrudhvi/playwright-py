import pytest


@pytest.mark.parametrize("url, title", [
    ("https://www.google.com", "Google"),
    ("https://www.bing.com", "Search - Microsoft Bing")
])
def test_search_engines(page, url, title):
    page.goto(url)
    assert title in page.title()
