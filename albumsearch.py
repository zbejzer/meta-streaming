from picard.config import get_config
from picard.mbjson import (
    countries_from_node,
    media_formats_from_node,
    release_group_to_metadata,
    release_to_metadata,
)
from picard.metadata import Metadata
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog import Retry

from picard.plugins.metastreaming.api_helpers import build_deezer_query, DeezerAPIHelper


class StreamingAlbumSearchDialog(AlbumSearchDialog):
    def search(self, text):
        """Perform search using query provided by the user."""
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        self.deezer_api = DeezerAPIHelper(self.tagger.webservice)
        self.deezer_api.find(
            self.handle_reply,
            query=text,
            search=True,
            advanced_search=self.use_advanced_search,
        )

    def show_similar_albums(self, cluster):
        """Perform search by using existing metadata information
        from the cluster as query."""
        self.cluster = cluster
        metadata = cluster.metadata
        query = {
            "artist": metadata["albumartist"],
            "album": metadata["album"],
        }

        # If advanced query syntax setting is enabled by user, query in
        # advanced syntax style. Otherwise query only album title.
        if self.use_advanced_search:
            query_str = build_deezer_query(query)
        else:
            query_str = query["album"]
        self.search(query_str)

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            releases = document["data"]
            if releases.len() < 1:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            self.no_results_found()
            return

        del self.search_results[:]
        self.parse_releases(releases)
        self.display_results()
        self.fetch_coverarts()

    def fetch_coverart(self, cell):
        # FIXME: implement cover art fetching
        return

    def parse_releases(self, releases):
        for node in releases:
            release = Metadata()
            release_to_metadata(node, release)
            release["score"] = node["score"]
            rg_node = node["release-group"]
            release_group_to_metadata(rg_node, release)
            if "media" in node:
                media = node["media"]
                release["format"] = media_formats_from_node(media)
                release["tracks"] = node["track-count"]
            countries = countries_from_node(node)
            if countries:
                release["country"] = countries_shortlist(countries)
            self.search_results.append(release)
