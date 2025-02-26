import pytest


@pytest.mark.smoke
def test_google(page):
    page.goto("https://www.google.com")
    assert "Google" in page.title()


def test_bing(page):
    page.goto("https://www.bing.com")
    assert "Search - Microsoft Bing" in page.title()
