from datetime import datetime
from typing import List

from ffmpeg import FFmpeg, Progress
from mutagen.easyid3 import EasyID3
from tqdm import tqdm

from podsync.sources.mp3 import Mp3
from podsync.sources.playerfm import Playerfm
from podsync.sources.source import Source

__all__ = ["download"]


def download(url: str, path: str):
    # Find the source
    sources: List[Source] = [Playerfm(), Mp3()]
    source = next((source for source in sources if source.applicable(url)), None)
    if source is None:
        raise ValueError("Unknown podcast type")

    print("Downloading a podcast from", url, "to", path, "using", source.__class__.__name__)

    # Read metadata
    metadata = source.read(url)

    # Download and transform the file
    full_path = path + "/" + metadata["filename"]
    _ffmpeg_download(
        url=metadata["url"],
        file=full_path,
        speedup=1.4,
        duration_seconds=metadata.get("duration_seconds"),
    )

    # Set file ID3 metadata
    id3_data = EasyID3()
    id3_data["title"] = metadata.get("episode_title") or "Unknown podcast"
    id3_data["album"] = metadata.get("series_title") or "Unknown podcast"
    id3_data["artist"] = metadata.get("series_title") or "Unknown podcast"
    id3_data["date"] = (metadata.get("date_published") or datetime.today()).isoformat()
    id3_data["genre"] = "Podcast"
    id3_data.save(full_path)


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
        if duration_seconds is not None:
            progress_bar.n = int(progress.time.total_seconds())
        progress_bar.refresh()

    @ffmpeg.on("completed")
    def on_completed():
        if duration_seconds is not None:
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
