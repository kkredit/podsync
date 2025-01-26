from datetime import datetime
from typing import List

from ffmpeg import FFmpeg, Progress
from mutagen.easyid3 import EasyID3
from pyffmpeg import FFprobe
from tqdm import tqdm

from podsync.config import Config
from podsync.sources.direct import Direct
from podsync.sources.playerfm import Playerfm
from podsync.sources.source import Source
from podsync.sources.youtube import Youtube

__all__ = ["download"]


def download(config: Config, url: str):
    # Find the source
    sources: List[Source] = [Playerfm(), Youtube(), Direct()]
    source = next((source for source in sources if source.applicable(url)), None)
    if source is None:
        raise ValueError("Unknown podcast type")

    print(
        "Downloading a podcast from",
        url,
        "using",
        source.__class__.__name__,
    )

    # Read metadata
    metadata = source.read(url)
    series_config = config.for_series(metadata.get("series_title"))

    if series_config.verbose:
        print("Series config:", series_config)
        print("Metadata:", metadata)

    # Download and transform the file
    full_path = series_config.download_path + "/" + metadata["filename"]
    _ffmpeg_download(
        url=metadata["url"],
        file=full_path,
        speedup=series_config.speedup,
        duration_seconds=metadata.get("duration_seconds"),
        verbose=series_config.verbose,
    )

    # Set file ID3 metadata
    id3_data = EasyID3()
    id3_data["title"] = metadata.get("episode_title") or "Unknown podcast"
    id3_data["album"] = metadata.get("series_title") or "Unknown podcast"
    id3_data["artist"] = metadata.get("series_title") or "Unknown podcast"
    id3_data["date"] = (metadata.get("date_published") or datetime.today()).isoformat()
    id3_data["genre"] = "Podcast"
    id3_data.save(full_path)


def _ffmpeg_download(
    url: str, file: str, speedup: float, duration_seconds: int | None, verbose: int
):
    # capture output to a variable
    #  ffprobe = FFmpeg().input(url).option("v", "quiet").option("print_format", "json").option("show_format", None)
    # capture output to a variable
    #  ffprobe = FFprobe(url)
    #  if verbose:
    #  print("FFprobe result:", ffprobe.metadata)
    #  print("input duration:", duration_seconds)
    #  exit(0)

    #  duration_seconds = duration_seconds or int(probe["format"]["duration"])

    ffmpeg = (
        FFmpeg()
        .input(url)
        .output(file, {"filter:a": f"atempo={speedup}"})
        .option("y")
        .option("loglevel", "debug" if verbose else "info")
    )
    if verbose:
        print("FFmpeg command:", " ".join(ffmpeg.arguments))
    stderr_lines = []

    progress_bar = tqdm(
        total=duration_seconds, unit="s", desc="Processing", dynamic_ncols=True
    )

    @ffmpeg.on("start")
    def on_start(arguments: list[str]):
        if verbose:
            print("FFmpeg started with arguments:", arguments)

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
