from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.core.version import APP_VERSION, GITHUB_OWNER, GITHUB_REPO


@dataclass
class Release:
    name: str
    tag_name: str
    published_at: str
    html_url: str
    body: str
    download_url: Optional[str]
    assets: list[dict[str, str]]


# In-memory cache for GitHub latest release to avoid hitting the GitHub rate
# limit on every click. The HTML page is used instead of the REST API because
# the unauthenticated API is limited to 60 requests/hour.
_update_cache: tuple[Release, bool, float] | None = None
CACHE_TTL = 300  # seconds


def _norm_version(v: str) -> list[int]:
    v = (v or "").lstrip("vV").split("-")[0]
    parts = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except ValueError:
            parts.append(0)
    return parts


def compare_version(current: str, latest: str) -> bool:
    """Return True if `latest` is strictly newer than `current`.

    Pre-release tags (containing '-') are ignored.
    """
    if "-" in latest:
        return False
    a, b = _norm_version(current), _norm_version(latest)
    n = max(len(a), len(b))
    a += [0] * (n - len(a))
    b += [0] * (n - len(b))
    return b > a


async def _fetch_page(url: str, timeout: float) -> str:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
    resp.raise_for_status()
    return resp.text


async def get_latest_release(timeout: float = 5) -> Release:
    """Parse the latest release from the GitHub releases HTML page.

    GitHub's REST API has a very low unauthenticated rate limit, so we scrape
    the public releases page instead.
    """
    releases_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
    html = await _fetch_page(releases_url, timeout)
    soup = BeautifulSoup(html, "html.parser")

    tag_link = soup.find(
        "a",
        href=re.compile(rf"^/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/"),
    )
    if not tag_link:
        raise ValueError("Could not find release tag on GitHub releases page")

    href = tag_link.get("href", "")
    tag_name = href.split("/")[-1]
    html_url = f"https://github.com{href}"
    name = tag_link.text.strip()

    published_at = ""
    body = ""
    section = tag_link.find_parent("section")
    if section:
        time_tag = section.find("relative-time")
        if time_tag:
            published_at = (time_tag.get("datetime") or "").replace("T", " ").replace("Z", "")
        body_tag = section.find("div", class_="markdown-body")
        if body_tag:
            body = body_tag.get_text("\n").strip()

    download_url = None
    assets: list[dict[str, str]] = []
    assets_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/expanded_assets/{tag_name}"
    try:
        assets_html = await _fetch_page(assets_url, timeout)
        assets_soup = BeautifulSoup(assets_html, "html.parser")
        asset_links = assets_soup.find_all(
            "a",
            href=re.compile(rf"^/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/"),
        )
        for asset_link in asset_links:
            href = asset_link.get("href", "")
            if href:
                assets.append({
                    "name": asset_link.text.strip(),
                    "url": f"https://github.com{href}",
                })
        if assets:
            download_url = assets[0]["url"]
    except Exception:
        # Assets are optional; if the page fails we still report the release.
        pass

    return Release(
        name=name,
        tag_name=tag_name,
        published_at=published_at,
        html_url=html_url,
        body=body,
        download_url=download_url,
        assets=assets,
    )


async def check_update(timeout: float = 5, force: bool = False) -> tuple[Optional[Release], bool]:
    """Fetch the latest release and whether it is newer than the running version.

    Results are cached for CACHE_TTL seconds to reduce requests to GitHub.
    Pass force=True to bypass the cache.
    """
    global _update_cache

    now = time.time()
    if not force and _update_cache is not None and (now - _update_cache[2]) < CACHE_TTL:
        return _update_cache[0], _update_cache[1]

    release = await get_latest_release(timeout=timeout)
    have_new = compare_version(APP_VERSION, release.tag_name)
    _update_cache = (release, have_new, now)
    return release, have_new


def invalidate_update_cache() -> None:
    """Clear the cached update result. Useful for tests."""
    global _update_cache
    _update_cache = None
