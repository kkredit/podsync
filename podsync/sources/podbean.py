from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from podsync.sources.helpers import html_content_by_attrs
from podsync.sources.source import DownloadMetadata, Source


class Podbean(Source):
    def applicable(self, url: str) -> bool:
        return "podbean.com" in url

    def read(self, url: str) -> DownloadMetadata:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML content
        html = BeautifulSoup(response.text, "html.parser")

        # Extract metadata
        metadata = html_content_by_attrs(
            html, "script", {"type": "application/ld+json"}
        )
        if metadata is None:
            with open("podbean-no-parse-mp3.html", "w") as f:
                f.write(response.text)
            raise ValueError(
                "Could not find metadata blob, see podbean-no-parse-mp3.html"
            )

        # Parse JSON
        parsed = PodbeanMetadata.model_validate_json(metadata)
        parsed_date = datetime.fromisoformat(parsed.datePublished)
        formatted_date = parsed_date.strftime("%Y.%m.%d")
        filename = f"{formatted_date}-{parsed.partOfSeries.name}-{parsed.name}.mp3"

        # Return metadata
        return {
            "url": parsed.associatedMedia.contentUrl,
            "filename": filename,
            "duration_seconds": None,
            "episode_title": parsed.name,
            "series_title": parsed.partOfSeries.name,
            "date_published": parsed_date,
        }


class PodbeanAssociatedMedia(BaseModel):
    contentUrl: str


class PodbeanPartOfSeries(BaseModel):
    name: str


class PodbeanMetadata(BaseModel):
    name: str
    datePublished: str
    associatedMedia: PodbeanAssociatedMedia
    partOfSeries: PodbeanPartOfSeries
