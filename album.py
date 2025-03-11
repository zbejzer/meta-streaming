import traceback

from PyQt5 import (
    QtCore,
    QtNetwork,
)

from picard import log
from picard.album import AlbumStatus, Album
from picard.config import get_config
from picard.metadata import Metadata
from picard.tagger import Tagger
from picard.album import ParseResult

from picard.plugins.metastreaming.providers import providers, ProviderNames
import picard.plugins.metastreaming.deezerjson as deezerjson


class StreamingAlbum(Album):
    tagger: Tagger | None = None

    def __init__(self, album_id: str):
        """album id should be the actual id from streaming"""
        self.streaming_id = album_id
        super().__init__(album_id)

    @property
    def id(self):
        return providers[ProviderNames.DEEZER].generate_release_UUID(self.streaming_id)

    @id.setter
    def id(self, value):
        log.warning("Attempted to set id attribute for %s", self.__class__)

    @id.deleter
    def id(self):
        log.warning("Attempted to delete id attribute for %s", self.__class__)

    @property
    def rg_id(self):
        return providers[ProviderNames.DEEZER].generate_releasegroup_UUID(self.streaming_id)

    def _parse_release(self, release_node):
        log.debug("Loading release %r …", self.id)
        self._tracks_loaded = False
        self._release_node = release_node
        assert isinstance(self.tagger, Tagger)

        # Get release metadata
        m = self._new_metadata
        m.length = 0

        rg = self.release_group = self.tagger.get_release_group_by_id(self.rg_id)
        rg.loaded_albums.add(self.id)
        rg.refcount += 1

        deezerjson.album_to_metadata(release_node, m, album=self)

        config = get_config()

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            m.apply_func(asciipunct)

        m['totaldiscs'] = len(release_node['media'])

        # Add album to collections
        add_release_to_user_collections(release_node)

        if config.setting['track_ars']:
            # Detect if track relationships did not get loaded
            try:
                for medium_node in release_node['media']:
                    if medium_node['track-count']:
                        if 'relations' in medium_node['tracks'][0]['recording']:
                            return ParseResult.PARSED
                        else:
                            return ParseResult.MISSING_TRACK_RELS
            except KeyError:
                pass

        return ParseResult.PARSED

    def _release_request_finished(self, document, http, error):
        if self.load_task is None:
            return
        self.load_task = None
        parse_result = None
        try:
            if error:
                self.error_append(http.errorString())
            else:
                try:
                    parse_result = self._parse_release(document)
                    self._run_album_metadata_processors()
                except Exception:
                    error = True
                    self.error_append(traceback.format_exc())
        finally:
            self._requests -= 1
            if parse_result == ParseResult.PARSED or error:
                self._finalize_loading(error)

    def load_from_deezer(self, priority=False, refresh=False):
        # TODO: Split this monstrosity

        assert isinstance(self.tagger, Tagger)
        if self._requests:
            log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message(
            N_("Loading album %(id)s …"),
            {'id': self.id}
        )
        self.loaded = False
        self.status = AlbumStatus.LOADING
        if self.release_group:
            self.release_group.loaded = False
            self.release_group.genres.clear()
        self.metadata.clear()
        self.genres.clear()
        self.update(update_selection=False)
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._requests = 1
        self.clear_errors()

        self.load_task = self.tagger.deezer_api.get_release_by_id(
            self.id,
            self._release_request_finished,
            priority=priority,
            refresh=refresh
        )
        return
