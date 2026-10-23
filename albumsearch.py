from functools import partial

from PyQt6 import QtGui

from picard import log
from picard.i18n import N_
from picard.plugin3.api import (
    Album,
    Metadata,
    PluginApi,
)
from picard.tagger import Tagger
from picard.util import restore_method

from .api_helpers import (
    DeezerAPIHelper,
    build_deezer_query,
)
from .deezerjson import albumsearch_to_metadata
from .providers import MetadataProvider

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

    def __init__(self, parent, force_advanced_search=None, existing_album=None):
        self.columns = Columns(
            (
                Column(N_("Name"), "album", sort_type=ColumnSortType.NAT, width=150),
                Column(N_("Artist"), "albumartist"),
                Column(N_("Tracks"), "tracks", sort_type=ColumnSortType.NAT, align=ColumnAlign.RIGHT),
                Column(N_("Source"), "source"),
                Column(N_("ID"), "deezer_albumid", sort_type=ColumnSortType.NAT, align=ColumnAlign.RIGHT),
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

    def search(self, text):
        """Perform search using query provided by the user."""
        if self.fetching:
            self.fetch_cleanup()
            self.fetching = False
        self.retry_params = Retry(self.search, text)
        self.search_box_text(text)
        self.show_progress()
        assert isinstance(self.tagger.deezer_api, DeezerAPIHelper)
        self.tagger.deezer_api.find(
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
        """Queue cover art from Deezer server for each album in search
        results.
        """
        if cell.fetched:
            return
        if not cell.is_visible():
            return
        cell.fetched = True
        deezerid = cell.mbid
        cell.fetch_task = self.tagger.webservice.download_url(
            url=f"{DeezerAPIHelper.API_URL}/album/{deezerid}/image?size=medium",
            handler=partial(self._cover_downloaded, cell),
        )

    def _cover_downloaded(self, cover_cell, data, http, error):
        """Handle cover art query reply from Deezer server.
        If server returns the cover image successfully, update the cover art
        cell of particular release.
        """
        cover_cell.fetch_task = None

        if error:
            cover_cell.not_found()
        else:
            pixmap = QtGui.QPixmap()
            try:
                pixmap.loadFromData(data)
                cover_cell.set_pixmap(pixmap)
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
                            release["deezer_albumid"],
                            cover_size,
                            on_show=self.fetch_coverart,
                        )
                    )
                else:
                    self.set_table_item_value(row, pos, c, release)
        self.show_table(sort_column="deezer_albumid")

    def accept_event(self, rows):
        for row in rows:
            self.load_selection(row)

    def load_selection(self, row):
        # Functionality from picard's AlbumSearchDialog.load_section
        release: Metadata = self.search_results[row]
        # generating IDs due to not being associated with any actual MB release
        provider: MetadataProvider = MetadataProvider(MetadataProvider.Names.DEEZER, str(release["deezer_albumid"]))
        release_mbid = str(provider.generate_release_UUID())
        rg_mbid = str(provider.generate_releasegroup_UUID())
        if self.existing_album:
            # No need to implement for now as StreamingAlbumSearchDialog can only be invoked for Clusters
            # self.existing_album.switch_release_version(release_mbid)
            raise NotImplementedError
        else:
            assert isinstance(self.tagger, Tagger)
            self.tagger.get_release_group_by_id(rg_mbid).loaded_albums.add(release_mbid)
            # Functionality from picard's Tagger.load_album
            album = self.tagger.albums.get(release_mbid)
            if album:
                log.debug("Album %s already loaded.", release_mbid)
            else:
                album = Album(release_mbid)
                self.tagger.albums[release_mbid] = album
                self.tagger.album_added.emit(album)
                album.metastreaming_provider = provider  # pyright: ignore[reportAttributeAccessIssue]
                album.load_from_deezer()  # FIXME: replace with a non-dynamically added function      #pyright: ignore[reportAttributeAccessIssue]
            # Functionality from picard's AlbumSearchDialog.load_selection
            if self.cluster:
                files = self.cluster.iterfiles()
                self.tagger.move_files_to_album(files, release_mbid, album)
