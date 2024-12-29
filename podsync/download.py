from datetime import datetime
from urllib.request import urlretrieve

import requests
from bs4 import BeautifulSoup
from ffmpeg import FFmpeg, Progress

#  from pydub import AudioSegment
#  from pydub.effects import speedup

__all__ = ["download"]


def download(url: str, path: str):
    print("Downloading a podcast from", url, "to", path)

    if ".mp3" in url:
        download_mp3(url, path)
    elif "player.fm" in url:
        download_playerfm(url, path)
    else:
        print("Unknown podcast type")


def download_mp3(url: str, path: str):
    urlretrieve(url, path)


def download_playerfm(url: str, path: str):
    # Fetch the webpage content
    response = requests.get(url)
    response.raise_for_status()

    # Parse HTML content
    html = BeautifulSoup(response.text, "html.parser")

    # Extract metadata
    series_title = _playerfm_series_title_from_html(html) or "Unknown Series"
    episode_title = _playerfm_episode_title_from_html(html) or "Unknown Episode"
    date_published = _playerfm_episode_published_from_html(html)
    mp3_url = _mp3_url_from_html(html)
    if mp3_url is None:
        raise ValueError("Could not find mp3 URL")

    # Download the mp3 file
    print("Downloading", series_title, "-", episode_title, "...")
    filename = path + "/" + f"{date_published}-{series_title} - {episode_title}.mp3"

    ffmpeg = FFmpeg().input(mp3_url).output(filename, filter="atempo=1.5").option("y")

    @ffmpeg.on("progress")
    def on_progress(progress: Progress):
        print(progress)

    @ffmpeg.on("stderr")
    def on_stderr(stderr: str):
        print("stderr:", stderr)

    ffmpeg.execute()

    print("Downloaded to", filename, "!")


def _playerfm_series_title_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"property": "og:site_name"})


def _playerfm_episode_title_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"property": "og:title"})


def _mp3_url_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"name": "twitter:player:stream"})


def _playerfm_episode_published_from_html(html: BeautifulSoup) -> str:
    ts = _meta_content_by_attrs(html, {"property": "og:updated_time"})
    if ts is None:
        return datetime.today().strftime("%Y.%m.%d")  # fallback to today
    return datetime.fromisoformat(ts).strftime("%Y.%m.%d")


def _meta_content_by_attrs(html: BeautifulSoup, attrs: dict[str, str]) -> str | None:
    tag = html.find("meta", attrs=attrs)
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    content = tag.get("content")
    return content[0] if isinstance(content, list) else content
