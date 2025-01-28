from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    get_config,
)
from picard.mbjson import (
    countries_from_node,
    media_formats_from_node,
    release_group_to_metadata,
    release_to_metadata,
)
from picard.metadata import Metadata
from picard.ui.searchdialog.album import AlbumSearchDialog, CoverCell
from picard.ui.searchdialog import Retry, SearchDialog
from picard.util import countries_shortlist

from picard.plugins.metastreaming.api_helpers import build_deezer_query, DeezerAPIHelper
from picard.plugins.metastreaming.deezerjson import albumsearch_to_metadata


class StreamingAlbumSearchDialog(SearchDialog):

    dialog_header_state = "streamingalbumsearchdialog_header_state"

    options = [Option("persist", dialog_header_state, QtCore.QByteArray())]

    def __init__(self, parent, force_advanced_search=None, existing_album=None):
        super().__init__(
            parent,
            accept_button_title=_("Load into Picard"),
            search_type="album",
            force_advanced_search=force_advanced_search,
        )
        self.cluster = None
        self.existing_album = existing_album
        self.setWindowTitle(_("Streaming Album Search Results"))
        self.columns = [
            ("name", _("Name")),
            ("artist", _("Artist")),
            ("tracks", _("Tracks")),
            ("id", _("ID")),
            ("cover", _("Cover")),
        ]
        self.cover_cells = []
        self.fetching = False
        self.scrolled.connect(self.fetch_coverarts)

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

    def retry(self):
        self.retry_params.function(self.retry_params.query)

    def handle_reply(self, document, http, error):
        if error:
            self.network_error(http, error)
            return

        try:
            releases: list = document["data"]
            if len(releases) < 1:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            self.no_results_found()
            return

        del self.search_results[:]
        self.parse_releases(releases)
        self.display_results()
        self.fetch_coverarts()

    def fetch_coverarts(self):
        if self.fetching:
            return
        self.fetching = True
        for cell in self.cover_cells:
            self.fetch_coverart(cell)
        self.fetching = False

    def fetch_coverart(self, cell):
        # FIXME: implement cover art fetching
        return

    def fetch_cleanup(self):
        for cell in self.cover_cells:
            if cell.fetch_task is not None:
                log.debug(
                    "Removing cover art fetch task for %s",
                    cell.release["musicbrainz_albumid"],
                )
                self.tagger.webservice.remove_task(cell.fetch_task)

    def closeEvent(self, event):
        if self.cover_cells:
            self.fetch_cleanup()
        super().closeEvent(event)

    def parse_releases(self, releases: list):
        for node in releases:
            release = Metadata()
            albumsearch_to_metadata(node, release)
            self.search_results.append(release)

    def display_results(self):
        self.prepare_table()
        self.cover_cells = []
        column = self.colpos("cover")
        for row, release in enumerate(self.search_results):
            self.table.insertRow(row)
            self.set_table_item(row, "name", release, "album")
            self.set_table_item(row, "artist", release, "albumartist")
            self.set_table_item(row, "tracks", release, "tracks")
            self.set_table_item(row, "id", release, "deezer_albumid")
            self.cover_cells.append(
                CoverCell(self.table, release, row, column, on_show=self.fetch_coverart)
            )
        self.show_table(sort_column="id")

    def accept_event(self, rows):
        for row in rows:
            self.load_selection(row)

    def load_selection(self, row):
        return
        # release = self.search_results[row]
        # release_mbid = release['musicbrainz_albumid']
        # if self.existing_album:
        #     self.existing_album.switch_release_version(release_mbid)
        # else:
        #     self.tagger.get_release_group_by_id(
        #         release['musicbrainz_releasegroupid']).loaded_albums.add(
        #             release_mbid)
        #     album = self.tagger.load_album(release_mbid)
        #     if self.cluster:
        #         files = self.cluster.iterfiles()
        #         self.tagger.move_files_to_album(files, release_mbid, album)
