import re

from PyQt5.QtCore import QUrl

from picard.config import get_config
from picard.webservice.api_helpers import APIHelper


def escape_deezer_query(text):
    # FIXME: actually ensure a proper query. It's just a placeholder really
    return re.sub(r'(")', r"", text)


def build_deezer_query(args):
    return " ".join(
        '%s:"%s"' % (item, escape_deezer_query(value))
        for item, value in args.items()
        if value
    )


class DeezerAPIHelper(APIHelper):
    @property
    def base_url(self):
        # FIXME: Make configurable
        return QUrl("https://api.deezer.com")

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
            f"/search",
            handler,
            unencoded_queryargs=filters,
            priority=True,
            important=True,
            mblogin=False,
            refresh=False,
        )
