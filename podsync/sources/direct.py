from datetime import datetime

from podsync.sources.source import DownloadMetadata, Source


class Direct(Source):
    def applicable(self, url: str) -> bool:
        return ".mp3" in url or ".aac" in url

    def read(self, url: str) -> DownloadMetadata:
        today = datetime.today()
        file_base_name = url.split("/")[-1]
        return {
            "url": url,
            "filename": f"{today.strftime('%Y.%m.%d')}-{file_base_name}",
            "episode_title": file_base_name,
        }
