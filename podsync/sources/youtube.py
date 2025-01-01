from datetime import datetime

from pytube import YouTube

from podsync.sources.source import DownloadMetadata, Source


class Youtube(Source):
    def applicable(self, url: str) -> bool:
        return "youtube.com" in url

    def read(self, url: str) -> DownloadMetadata:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True, file_extension="aac").first()
        if stream is None:
            raise ValueError("Could not find audio stream")

        # TODO: add progress bar
        print("Downloading", yt.title, "...")
        temp_filename = stream.download(filename="temp")

        channel = yt.author
        title = yt.title
        date_published = yt.publish_date or datetime.today()

        return {
            #  "url": stream.url,
            "url": temp_filename,
            "filename": f"{date_published.strftime('%Y.%m.%d')}-{channel}-{title}.aac",
            "duration_seconds": yt.length,
            "episode_title": title,
            "series_title": channel,
            "date_published": date_published,
        }
