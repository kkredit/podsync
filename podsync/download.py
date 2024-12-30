from datetime import datetime, timedelta
from urllib.request import urlretrieve

import requests
from bs4 import BeautifulSoup
from ffmpeg import FFmpeg, Progress
from tqdm import tqdm

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
    series_title = _playerfm_series_title_from_html(html)
    episode_title = _playerfm_episode_title_from_html(html)
    date_published = _playerfm_episode_published_from_html(html)
    duration_seconds = _playerfm_episode_duration_seconds_from_html(html)
    mp3_url = _mp3_url_from_html(html)
    if mp3_url is None:
        raise ValueError("Could not find mp3 URL")

    # Download the mp3 file
    #  print("Downloading", series_title, "-", episode_title, "...")
    filename = path + "/" + f"{date_published}-{series_title}-{episode_title}.mp3"
    _ffmpeg_download(
        url=mp3_url, file=filename, speedup=1.4, duration_seconds=duration_seconds
    )


def _ffmpeg_download(url: str, file: str, speedup: float, duration_seconds: int | None):
    ffmpeg = FFmpeg().input(url).output(file, filter=f"atempo={speedup}").option("y")
    stderr_lines = []

    progress_bar = tqdm(
        total=duration_seconds, unit="s", desc="Processing", dynamic_ncols=True
    )

    @ffmpeg.on("start")
    def on_start(arguments: list[str]):
        #  print("FFmpeg started with arguments:", arguments)
        pass

    @ffmpeg.on("progress")
    def on_progress(progress: Progress):
        #  print("FFmpeg progress:", progress)
        #  current = getattr(progress, "time", timedelta()).total_seconds()
        progress_bar.n = int(progress.time.total_seconds())
        progress_bar.refresh()

    @ffmpeg.on("completed")
    def on_completed():
        progress_bar.n = progress_bar.total
        progress_bar.refresh()
        progress_bar.close()
        print("Processing completed!")
        print("File saved to", file)

    @ffmpeg.on("stderr")
    def on_stderr(stderr: str):
        stderr_lines.append(stderr)

    @ffmpeg.on("terminated")
    def on_terminated():
        progress_bar.close()
        print("Processing terminated!")
        print("STDERR: ", "\n".join(stderr_lines))

    # if control-c is pressed, terminate the ffmpeg process
    try:
        ffmpeg.execute()
    except KeyboardInterrupt:
        ffmpeg.terminate()


def _playerfm_series_title_from_html(html: BeautifulSoup) -> str:
    return (
        _meta_content_by_attrs(html, {"property": "og:site_name"}) or "Unknown Series"
    )


def _playerfm_episode_title_from_html(html: BeautifulSoup) -> str:
    return _meta_content_by_attrs(html, {"property": "og:title"}) or "Unknown Episode"


def _mp3_url_from_html(html: BeautifulSoup) -> str | None:
    return _meta_content_by_attrs(html, {"name": "twitter:player:stream"})


def _playerfm_episode_published_from_html(html: BeautifulSoup) -> str:
    ts = _meta_content_by_attrs(html, {"property": "og:updated_time"})
    if ts is None:
        return datetime.today().strftime("%Y.%m.%d")  # fallback to today
    return datetime.fromisoformat(ts).strftime("%Y.%m.%d")


def _playerfm_episode_duration_seconds_from_html(html: BeautifulSoup) -> int | None:
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
