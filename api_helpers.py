from enum import StrEnum
import re
from typing import Callable

from PyQt5.QtCore import QUrl

from picard.config import get_config
from picard.webservice.api_helpers import APIHelper

_DEEZERAPI_URL: str = "https://api.deezer.com"


# TODO: Join this with the Provider class or something


def escape_deezer_query(text):
    # FIXME: actually ensure a proper query. It's just a placeholder really
    return re.sub(r'(")', r"", text)


def build_deezer_query(args):
    return " ".join(
        '%s:"%s"' % (item, escape_deezer_query(value))
        for item, value in args.items()
        if value
    )


class DeezerAPIObject(StrEnum):
    ALBUM = "album"
    ARTIST = "artist"
    TRACK = "track"


class DeezerAPIHelper(APIHelper):
    # TODO: Make URL configurable
    # TODO: Replace with universal class / subclass hierarchy for easier implementation of other streamings

    API_URL: str = _DEEZERAPI_URL

    def __init__(self, webservice):
        super().__init__(webservice, self.API_URL)

    def find(self, handler, **kwargs):
        filters = {}

        is_search = kwargs.pop("search", False)
        if is_search:
            config = get_config()
            use_advanced_search = kwargs.pop(
                "advanced_search", config.setting["use_adv_search_syntax"]
            )
            if use_advanced_search:
                query = kwargs["query"]
            else:
                query = escape_deezer_query(kwargs["query"]).strip()
        else:
            query = build_deezer_query(kwargs)

        if query:
            filters["q"] = query

        return self.get(
            f"/search/album",
            handler,
            unencoded_queryargs=filters,
            priority=True,
            important=True,
            mblogin=False,
            refresh=False,
        )

    def _get_by_id(self, entitytype, entityid, handler, **kwargs):
        return self.get(f"/{entitytype}/{entityid}", handler, **kwargs)

    def get_release_by_id(self, releaseid: str, handler: Callable, **kwargs):
        return self._get_by_id(DeezerAPIObject.ALBUM, releaseid, handler, **kwargs)
