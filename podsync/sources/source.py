from datetime import datetime
from typing import NotRequired, Protocol, TypedDict


class DownloadMetadata(TypedDict):
    url: str
    filename: str
    duration_seconds: NotRequired[int | None]
    episode_title: NotRequired[str]
    series_title: NotRequired[str]
    date_published: NotRequired[datetime]


class Source(Protocol):
    def applicable(self, url: str) -> bool:
        ...

    def read(self, url: str) -> DownloadMetadata:
        ...
