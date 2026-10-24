from functools import partial
from typing import ClassVar

from PyQt6 import (
    QtGui,
    QtWidgets,
)

from picard import log
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.plugin3.api import (
    Metadata,
    PluginApi,
)
from picard.util import restore_method

from .album import load_deezer_album
from .api_helpers import (
    DeezerAPIHelper,
    build_deezer_query,
)
from .deezerjson import albumsearch_to_metadata

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
)
from picard.ui.searchdialog import (
    Retry,
    SearchDialog,
)
from picard.ui.searchdialog.album import (
    CoverCell,
    CoverColumn,
)


class StreamingAlbumSearchDialog(SearchDialog):
    dialog_header_state = "streamingalbumsearchdialog_header_state"
    _cover_cache: ClassVar[dict[str, QtGui.QPixmap]] = {}

    def __init__(self, parent, force_advanced_search=None, existing_album=None):
        self.columns = Columns(
            (
                Column(N_("Name"), "album", sort_type=ColumnSortType.NAT, width=150),
                Column(N_("Artist"), "albumartist"),
                Column(N_("Tracks"), "tracks", sort_type=ColumnSortType.NAT, align=ColumnAlign.RIGHT),
                Column(N_("Source"), "source"),
                Column(N_("ID"), "deezer_album_id", sort_type=ColumnSortType.NAT, align=ColumnAlign.RIGHT),
                CoverColumn(N_("Cover"), "cover", width=100),
            ),
            default_width=100,
        )
        super().__init__(
            parent,
            N_("Streaming Album Search Results"),
            accept_button_title=N_("Load into Picard"),
            search_type="album",
            force_advanced_search=force_advanced_search,
        )
        self.cluster = None
        self.existing_album = existing_album
        self.cover_cells = []
        self.fetching = False
        self.scrolled.connect(self.fetch_coverarts)
        self.resized.connect(self.fetch_coverarts)

        # Search pagination state
        self.current_index = 0
        self.results_limit = 25
        self.total_results = 0
        self.current_query = ""

        # Load More button
        self.load_more_button = QtWidgets.QPushButton(_("Load More"), self.buttonBox)
        self.load_more_button.setVisible(False)
        self.buttonBox.addButton(self.load_more_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.load_more_button.clicked.connect(self.load_more_results)

    @restore_method
    def restore_table_header_state(self):
        api = PluginApi.get_api()
        state = api.plugin_persist[self.dialog_header_state]
        if state:
            self.header().restoreState(state)
            log.debug("restore_state: %s", self.dialog_header_state)

    def save_table_header_state(self):
        state = self.header().saveState()
        api = PluginApi.get_api()
        api.plugin_persist[self.dialog_header_state] = state
        log.debug("save_state: %s", self.dialog_header_state)

    def search(self, text, index=0):
        """Perform search using query provided by the user."""
        if self.fetching:
            self.fetch_cleanup()
            self.fetching = False

        self.current_index = index
        if index == 0:
            self.current_query = text
            del self.search_results[:]
            self.load_more_button.setVisible(False)
            self.show_progress()
        else:
            self.load_more_button.setEnabled(False)

        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        api = PluginApi.get_api()
        deezer_api = DeezerAPIHelper(api.web_service)
        deezer_api.find(
            self.handle_reply,
            query=text,
            search=True,
            advanced_search=self.use_advanced_search,
            index=index,
            limit=self.results_limit,
        )

    def load_more_results(self):
        """Fetch next page of search results."""
        if self.current_query:
            next_index = self.current_index + self.results_limit
            self.search(self.current_query, index=next_index)

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
            self.total_results = document.get("total", len(releases))
            if len(releases) < 1 and not self.search_results:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            self.no_results_found()
            return

        # Advance current index if this was a paginated request
        if "next" in document or len(releases) > 0:
            if "total" in document:
                self.total_results = document["total"]

        self.parse_releases(releases)
        self.display_results()
        self.fetch_coverarts()

        # Update Load More button state
        loaded_count = len(self.search_results)
        if loaded_count < self.total_results and len(releases) > 0:
            self.load_more_button.setText(
                _("Load More ({count}/{total})").format(count=loaded_count, total=self.total_results)
            )
            self.load_more_button.setEnabled(True)
            self.load_more_button.setVisible(True)
        else:
            self.load_more_button.setVisible(False)

    def fetch_coverarts(self):
        if self.fetching:
            return
        self.fetching = True
        for cell in self.cover_cells:
            self.fetch_coverart(cell)
        self.fetching = False

    def fetch_coverart(self, cell):
        """Queue cover art from Deezer server for each album in search
        results, utilizing in-memory thumbnail cache if available.
        """
        if cell.fetched:
            return
        if not cell.is_visible():
            return

        deezerid = cell.mbid
        if deezerid in self._cover_cache:
            cell.fetched = True
            cell.set_pixmap(self._cover_cache[deezerid])
            return

        cell.fetched = True
        cell.fetch_task = self.tagger.webservice.download_url(
            url=f"{DeezerAPIHelper.API_URL}/album/{deezerid}/image?size=medium",
            handler=partial(self._cover_downloaded, cell),
        )

    def _cover_downloaded(self, cover_cell, data, http, error):
        """Handle cover art query reply from Deezer server.
        If server returns the cover image successfully, update the cover art
        cell of particular release and cache the pixmap.
        """
        cover_cell.fetch_task = None

        if error:
            cover_cell.not_found()
        else:
            pixmap = QtGui.QPixmap()
            try:
                if pixmap.loadFromData(data):
                    self._cover_cache[cover_cell.mbid] = pixmap
                    cover_cell.set_pixmap(pixmap)
                else:
                    cover_cell.not_found()
            except Exception as e:
                cover_cell.not_found()
                log.error(e)

    def fetch_cleanup(self):
        for cell in self.cover_cells:
            if cell.fetch_task is not None:
                log.debug(
                    "Removing cover art fetch task for %s",
                    cell.mbid,
                )
                self.tagger.webservice.abort_task(cell.fetch_task)
                cell.fetch_task = None

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
        cover_pos = self.columns.pos("cover")
        cover_size = self.columns[cover_pos].width
        vheader = self.table.verticalHeader()
        vheader.setDefaultSectionSize(cover_size)
        for row, release in enumerate(self.search_results):
            self.table.insertRow(row)
            for pos, c in enumerate(self.columns):
                if isinstance(c, CoverColumn):
                    self.cover_cells.append(
                        CoverCell(
                            self.table,
                            row,
                            pos,
                            release["deezer_album_id"],
                            cover_size,
                            on_show=self.fetch_coverart,
                        )
                    )
                else:
                    self.set_table_item_value(row, pos, c, release)
        self.show_table(sort_column="deezer_album_id")

    def accept_event(self, rows):
        for row in rows:
            self.load_selection(row)

    def load_selection(self, row):
        release: Metadata = self.search_results[row]
        deezer_id = str(release["deezer_album_id"])
        api = PluginApi.get_api()
        load_deezer_album(api, deezer_id, cluster=self.cluster)
