"""Unit tests for the update checker."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core import updater
from app.core.version import APP_VERSION
from tests.conftest import AUTH


@pytest.fixture(autouse=True)
def _clear_update_cache():
    updater.invalidate_update_cache()


@pytest.mark.parametrize(
    "current,latest,expected",
    [
        ("2.0.0", "2.0.1", True),
        ("2.0.0", "2.0.0", False),
        ("2.0.0", "1.9.9", False),
        ("v2.0.0", "V2.0.1", True),
        ("2.0.0-beta", "2.0.1", True),
        ("2.0.0", "2.1.0-beta", False),  # pre-release latest is ignored
        ("1.10.0", "2.0.0", True),  # would be wrong with integer concatenation
        ("2.0", "2.0.0", False),
        ("2.0.0", "2.0.0.1", True),
    ],
)
def test_compare_version(current, latest, expected):
    assert updater.compare_version(current, latest) is expected


def _fake_releases_html(tag: str = "v9.9.9"):
    return f"""<!DOCTYPE html>
<html>
<body>
  <section aria-labelledby="release-heading">
    <h2 class="sr-only">Dockore {tag}</h2>
    <a class="Link--primary Link" href="/HsOjo/Dockore/releases/tag/{tag}">Dockore {tag}</a>
    <relative-time datetime="2026-01-01T00:00:00Z">Jan 1, 2026</relative-time>
    <div class="markdown-body">Release notes for {tag}</div>
  </section>
</body>
</html>"""


def _fake_assets_html(tag: str = "v9.9.9"):
    version = tag.lstrip("v")
    return f"""<!DOCTYPE html>
<html>
<body>
  <a href="/HsOjo/Dockore/releases/download/{tag}/Dockore_{version}_x64.dmg">Dockore_{version}_x64.dmg</a>
  <a href="/HsOjo/Dockore/releases/download/{tag}/Dockore_{version}_aarch64.dmg">Dockore_{version}_aarch64.dmg</a>
</body>
</html>"""


async def _mock_fetch_page(url: str, timeout: float) -> str:
    if "expanded_assets" in url:
        return _fake_assets_html()
    return _fake_releases_html()


async def test_get_latest_release_parses_html():
    with patch("app.core.updater._fetch_page", _mock_fetch_page):
        release = await updater.get_latest_release()
    assert release.tag_name == "v9.9.9"
    assert release.name == "Dockore v9.9.9"
    assert release.published_at == "2026-01-01 00:00:00"
    assert release.html_url == "https://github.com/HsOjo/Dockore/releases/tag/v9.9.9"
    assert release.download_url == "https://github.com/HsOjo/Dockore/releases/download/v9.9.9/Dockore_9.9.9_x64.dmg"
    assert len(release.assets) == 2
    assert release.assets[0]["name"] == "Dockore_9.9.9_x64.dmg"


async def test_check_update_returns_have_new():
    with patch("app.core.updater._fetch_page", _mock_fetch_page):
        release, have_new = await updater.check_update()
    assert release is not None
    assert have_new is True


async def test_check_update_respects_current_version():
    async def _mock_fetch_page_local(url: str, timeout: float) -> str:
        if "expanded_assets" in url:
            return _fake_assets_html(APP_VERSION)
        return _fake_releases_html(APP_VERSION)

    with patch("app.core.updater._fetch_page", _mock_fetch_page_local):
        release, have_new = await updater.check_update()
    assert release is not None
    assert have_new is False


async def test_check_update_caches_result():
    call_count = {"value": 0}

    async def _mock_fetch_page_counted(url: str, timeout: float) -> str:
        call_count["value"] += 1
        if "expanded_assets" in url:
            return _fake_assets_html()
        return _fake_releases_html()

    with patch("app.core.updater._fetch_page", _mock_fetch_page_counted):
        await updater.check_update()
        await updater.check_update()

    assert call_count["value"] == 2  # releases + assets once


async def test_check_update_force_bypasses_cache():
    call_count = {"value": 0}

    async def _mock_fetch_page_counted(url: str, timeout: float) -> str:
        call_count["value"] += 1
        if "expanded_assets" in url:
            return _fake_assets_html()
        return _fake_releases_html()

    with patch("app.core.updater._fetch_page", _mock_fetch_page_counted):
        await updater.check_update()
        await updater.check_update(force=True)

    assert call_count["value"] == 4  # (releases + assets) * 2


async def test_api_update_returns_result(client, monkeypatch):
    async def _mock_check_update(**kwargs):
        release = updater.Release(
            name="v9.9.9",
            tag_name="v9.9.9",
            published_at="2026-01-01 00:00:00",
            html_url="https://example.com",
            body="notes",
            download_url="https://example.com/app.zip",
            assets=[{"name": "app.zip", "url": "https://example.com/app.zip"}],
        )
        return release, True

    monkeypatch.setattr("app.api.update.check_update", _mock_check_update)
    resp = await client.get("/api/update", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["have_new"] is True
    assert data["latest"] == "v9.9.9"
    assert data["current"] == APP_VERSION
    assert data["assets"] == [{"name": "app.zip", "url": "https://example.com/app.zip"}]


async def test_api_update_returns_no_new(client, monkeypatch):
    async def _mock_check_update(**kwargs):
        release = updater.Release(
            name=APP_VERSION,
            tag_name=APP_VERSION,
            published_at="2026-01-01 00:00:00",
            html_url="https://example.com",
            body="notes",
            download_url=None,
            assets=[],
        )
        return release, False

    monkeypatch.setattr("app.api.update.check_update", _mock_check_update)
    resp = await client.get("/api/update", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["have_new"] is False
    assert data["current"] == APP_VERSION


async def test_api_update_returns_503_on_failure(client, monkeypatch):
    async def _mock_check_update(**kwargs):
        raise RuntimeError("GitHub page unavailable")

    monkeypatch.setattr("app.api.update.check_update", _mock_check_update)
    resp = await client.get("/api/update", headers=AUTH)
    assert resp.status_code == 503
    assert "GitHub page unavailable" in resp.json()["detail"]
