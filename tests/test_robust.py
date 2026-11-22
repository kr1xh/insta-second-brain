import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402
import weekly  # noqa: E402


class FakeBrowser:
    def __init__(self, url="https://www.instagram.com/p/A/"):
        self.url = url

    @asynccontextmanager
    async def page(self):
        class P:
            url = self.url

            async def content(self):
                return "<html></html>"
        yield P()


class SlowPost:
    @staticmethod
    async def fetch(page, id_or_url):
        raise TimeoutError("Page.goto: Timeout 30000ms exceeded.")


class OkPost:
    @staticmethod
    async def fetch(page, id_or_url):
        return "post"


def test_fetch_post_skips_a_timeout_instead_of_crashing():
    post, html, error = asyncio.run(sweep.fetch_post(FakeBrowser(), SlowPost, "A"))
    assert post is None and "Timeout" in error


def test_fetch_post_returns_post_and_page_html():
    post, html, error = asyncio.run(sweep.fetch_post(FakeBrowser(), OkPost, "A"))
    assert post == "post" and html == "<html></html>" and error is None


def test_fetch_post_still_stops_on_a_challenge_page():
    import pytest
    with pytest.raises(sweep.Blocked):
        asyncio.run(sweep.fetch_post(FakeBrowser("https://www.instagram.com/challenge/x/"), OkPost, "A"))


def test_weekly_children_run_without_a_console_window():
    flags = weekly.no_window_flags()
    if sys.platform == "win32":
        assert flags == 0x08000000  # CREATE_NO_WINDOW
    else:
        assert flags == 0
