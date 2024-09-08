import re
from typing import Any, Final
from abc import ABC, abstractmethod
import json
import urllib.request

from metastreaming.album import Album, Track


class WebHelper(ABC):
    API_URL: Final[str] = None
    URL_PATTERN: Final[str] = None

    def __init__(self):
        self.data: Album | Track = None

    def get_data(self, url: str) -> Album | Track:
        """Get data from URL and parse it into either Album or Track object"""
        url_args = self._parse_url(url)
        self._create_data_object(url_args)
        api_url = self._create_api_url(url_args)
        raw_data = self._get_data_from_api(api_url)
        return self._parse_raw_data(raw_data)

    def _parse_url(self, url: str) -> dict[str, Any]:
        """Extract parameters from a streaming service URL"""

        r = re.compile(self.URL_PATTERN)
        match = r.match(url)
        if match is not None:
            arguments = match.groupdict()
        else:
            arguments = None

        return arguments

    @abstractmethod
    def _create_data_object(self, args: dict[str, Any]) -> Album | Track:
        """Create object to store data"""
        pass

    @abstractmethod
    def _create_api_url(self, args: dict[str, Any]) -> str:
        """Create URL to service API request"""
        pass

    def _get_data_from_api(self, api_url: str) -> Any:
        try:
            response = urllib.request.urlopen(url=api_url).read()
            raw_data = json.loads(response)
        except urllib.error.URLError as e:
            raise ConnectionError(
                "Error occurred while fetching resource. Reason: " + e.reason
            )
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON syntax: ", e)
        except:
            raise BaseException("Unknown error occurred")
        return raw_data

    @abstractmethod
    def _parse_raw_data(self, raw_data: Any):
        """Parse raw data (i.e. json) obtained from API to either Album or Track object"""
        pass


class DeezerWebHelper(WebHelper):
    API_URL: Final[str] = "https://api.deezer.com"
    URL_PATTERN: Final[str] = (
        r"^https?://(?:www.)?deezer.com(?:/(?P<language>.+))?/(?P<service>[A-Za-z]+)/(?P<id>[A-Za-z0-9]+)"
    )

    def _create_data_object(self, args: dict[str, Any]):
        if args["service"] == "album":
            self.data = Album()
        elif args["service"] == "track":
            self.data = Track()

    def _create_api_url(self, args: dict[str, Any]) -> str:
        # https://api.deezer.com/version/service/id/method/?parameters
        if "parameters" not in args:
            return "{}/{}/{}".format(self.API_URL, args["service"], args["id"])
        else:
            return "{}/{}/{}{}".format(
                self.API_URL,
                args.service,
                args.id,
                args.parameters,
            )

    def _parse_track(self, raw_data: Any):
        # Dictionary where key is the name on deezer, and value name in code
        TRANSLATION_TABLE = {
            "title": "title",
            "isrc": "isrc",
            "release_date": "release_date",
            "track_position": "track_number",
            "disk_number": "disc_number",
            "bpm": "bpm",
            "gain": "gain",
        }

        if "contributors" in raw_data and len(raw_data["contributors"]) > 0:
            for contributor in raw_data["contributors"]:
                self.data.artist.append(contributor["name"])
        for tag in TRANSLATION_TABLE:
            if tag in raw_data:
                setattr(self.data, TRANSLATION_TABLE[tag], raw_data[tag])

    def _parse_album(self, raw_data: Any):
        # Dictionary where key is the name on deezer, and value name in code
        TRANSLATION_TABLE = {
            "title": "title",
            "upc": "upc",
            "label": "label",
            "release_date": "release_date",
        }

        if "contributors" in raw_data and len(raw_data["contributors"]) > 0:
            for contributor in raw_data["contributors"]:
                self.data.artist.append(contributor["name"])
        for tag in TRANSLATION_TABLE:
            if tag in raw_data:
                setattr(self.data, TRANSLATION_TABLE[tag], raw_data[tag])
        for track in raw_data["tracks"]["data"]:
            track_web_helper = DeezerWebHelper()
            track_web_helper.get_data(track["link"])
            track_data = track_web_helper.data
            self.data.tracks.append(track_data)

    def _parse_raw_data(self, raw_data: Any):
        if type(self.data) is Album:
            self._parse_album(raw_data)
        elif type(self.data) is Track:
            self._parse_track(raw_data)
