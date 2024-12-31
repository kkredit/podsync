from datetime import datetime

import requests
from bs4 import BeautifulSoup

from podsync.sources.source import DownloadMetadata, Source


class Playerfm(Source):
    def applicable(self, url: str) -> bool:
        return "player.fm" in url

    def read(self, url: str) -> DownloadMetadata:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML content
        html = BeautifulSoup(response.text, "html.parser")

        # Extract metadata
        series_title = _series_title_from_html(html)
        episode_title = _episode_title_from_html(html)
        date_published = _episode_published_from_html(html)
        duration_seconds = _episode_duration_seconds_from_html(html)
        mp3_url = _mp3_url_from_html(html)
        if mp3_url is None:
            with open("playerfm-no-parse-mp3.html", "w") as f:
                f.write(response.text)
            raise ValueError("Could not find mp3 URL, see playerfm-no-parse-mp3.html")

        # Download the mp3 file
        formatted_date = date_published.strftime("%Y.%m.%d")
        filename = f"{formatted_date}-{series_title}-{episode_title}.mp3"
        return {
            "url": mp3_url,
            "filename": filename,
            "duration_seconds": duration_seconds,
            "episode_title": episode_title,
            "series_title": series_title,
            "date_published": date_published,
        }


def _series_title_from_html(html: BeautifulSoup) -> str:
    return (
        _meta_content_by_attrs(html, {"property": "og:site_name"}) or "Unknown Series"
    )


def _episode_title_from_html(html: BeautifulSoup) -> str:
    return _meta_content_by_attrs(html, {"property": "og:title"}) or "Unknown Episode"


def _mp3_url_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"name": "twitter:player:stream"})


def _episode_published_from_html(html: BeautifulSoup) -> datetime:
    ts = _meta_content_by_attrs(html, {"property": "og:updated_time"})
    if ts is None:
        return datetime.today()
    return datetime.fromisoformat(ts)


def _episode_duration_seconds_from_html(html: BeautifulSoup) -> int | None:
    dur_str = _meta_content_by_attrs(html, {"property": "music:duration"})
    if dur_str is None:
        return None
    try:
        # string format is "mm:ss"
        minutes, seconds = map(int, dur_str.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        return None


def _meta_content_by_attrs(html: BeautifulSoup, attrs: dict[str, str]) -> str | None:
    tag = html.find("meta", attrs=attrs)
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    content = tag.get("content")
    return content[0] if isinstance(content, list) else content
