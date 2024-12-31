from datetime import datetime

from podsync.sources.source import DownloadMetadata, Source


class Mp3(Source):
    def applicable(self, url: str) -> bool:
        return ".mp3" in url

    def read(self, url: str) -> DownloadMetadata:
        today = datetime.today()
        mp3_base_name = url.split("/")[-1]
        return {
            "url": url,
            "filename": f"{today.strftime('%Y.%m.%d')}-{mp3_base_name}",
        }
