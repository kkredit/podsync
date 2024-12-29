from os import remove
from urllib.request import urlretrieve

import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment
from pydub.effects import speedup

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
    mp3_url = _mp3_url_from_html(html)
    if mp3_url is None:
        raise ValueError("Could not find mp3 URL")

    # Download the mp3 file
    filename = path + "/" + f"{series_title} - {episode_title}.mp3"
    orig_filename = filename + ".orig"
    urlretrieve(mp3_url, orig_filename)

    # Load the file into PyDub
    audio = AudioSegment.from_file(orig_filename)
    audio_fast = speedup(audio, playback_speed=1.5)

    # Save the file
    audio_fast.export(filename, format="mp3")

    # Remove the original file
    remove(orig_filename)


def _playerfm_series_title_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"property": "og:site_name"})


def _playerfm_episode_title_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"property": "og:title"})


def _mp3_url_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"name": "twitter:player:stream"})


def _meta_content_by_attrs(html: BeautifulSoup, attrs: dict[str, str]) -> str | None:
    tag = html.find("meta", attrs=attrs)
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    content = tag.get("content")
    return content[0] if isinstance(content, list) else content
