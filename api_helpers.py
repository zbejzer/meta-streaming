from abc import (
    ABC,
    abstractmethod,
)
from collections.abc import Callable
from enum import StrEnum
import re

from picard.config import get_config
from picard.webservice import WebService
from picard.webservice.api_helpers import APIHelper

from .providers import Provider


_DEEZERAPI_URL: str = "https://api.deezer.com"


def escape_deezer_query(text: str) -> str:
    return re.sub(r'(")', r"", text)


def build_deezer_query(args: dict) -> str:
    return " ".join('%s:"%s"' % (item, escape_deezer_query(value)) for item, value in args.items() if value)


class BaseStreamingAPIHelper(APIHelper, ABC):
    """Abstract base class for streaming service API helpers."""

    provider: Provider
    API_URL: str

    def __init__(self, webservice: WebService, base_url: str):
        super().__init__(webservice, base_url)

    @abstractmethod
    def search_albums(self, handler: Callable, query: str | dict, **kwargs):
        """Search for albums."""

    @abstractmethod
    def get_release_by_id(self, releaseid: str, handler: Callable, **kwargs):
        """Get album details by ID."""

    @abstractmethod
    def get_track_by_id(self, trackid: str, handler: Callable, **kwargs):
        """Get track details by ID."""

    @abstractmethod
    def get_album_cover_url(self, album_id: str, size: str = "xl") -> str:
        """Construct cover art URL for an album."""


class DeezerAPIObject(StrEnum):
    ALBUM = "album"
    ARTIST = "artist"
    TRACK = "track"


class DeezerAPIHelper(BaseStreamingAPIHelper):
    provider = Provider.DEEZER
    API_URL: str = _DEEZERAPI_URL

    def __init__(self, webservice: WebService):
        super().__init__(webservice, self.API_URL)

    def search_albums(self, handler: Callable, **kwargs):
        filters = {}

        is_search = kwargs.pop("search", False)
        if is_search:
            config = get_config()
            use_advanced_search = kwargs.pop("advanced_search", config.setting["use_adv_search_syntax"])
            query = kwargs["query"] if use_advanced_search else escape_deezer_query(kwargs["query"]).strip()
        elif isinstance(kwargs.get("query"), dict):
            query = build_deezer_query(kwargs["query"])
        else:
            query = kwargs.get("query", "")

        if query:
            filters["q"] = query

        if "index" in kwargs:
            filters["index"] = kwargs["index"]
        if "limit" in kwargs:
            filters["limit"] = kwargs["limit"]

        return self.get(
            "/search/album",
            handler,
            unencoded_queryargs=filters,
            priority=True,
            important=True,
            mblogin=False,
            refresh=False,
        )

    # Alias for backward compatibility
    def find(self, handler: Callable, **kwargs):
        return self.search_albums(handler, **kwargs)

    def _get_by_id(self, entitytype: str, entityid: str, handler: Callable, **kwargs):
        return self.get(f"/{entitytype}/{entityid}", handler, **kwargs)

    def get_release_by_id(self, releaseid: str, handler: Callable, **kwargs):
        return self._get_by_id(DeezerAPIObject.ALBUM, releaseid, handler, **kwargs)

    def get_track_by_id(self, trackid: str, handler: Callable, **kwargs):
        return self._get_by_id(DeezerAPIObject.TRACK, trackid, handler, **kwargs)

    def get_tracklist_by_id(self, releaseid: str, handler: Callable, **kwargs):
        return self._get_by_id(DeezerAPIObject.ALBUM, f"{releaseid}/tracks", handler, **kwargs)

    def get_album_cover_url(self, album_id: str, size: str = "xl") -> str:
        return f"{self.API_URL}/album/{album_id}/image?size={size}"


_API_HELPER_REGISTRY: dict[Provider, type[BaseStreamingAPIHelper]] = {
    Provider.DEEZER: DeezerAPIHelper,
}


def get_api_helper_for_provider(provider: Provider | str, webservice: WebService) -> BaseStreamingAPIHelper:
    """Instantiate and return the API helper for a specific streaming provider."""
    try:
        provider_enum = Provider(provider)
        return _API_HELPER_REGISTRY[provider_enum](webservice)
    except (ValueError, KeyError) as e:
        raise ValueError(f"No API helper registered for provider: {provider}") from e
