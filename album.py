from picard import log
from picard.album import AlbumStatus, Album
from picard.config import get_config
from picard.metadata import Metadata
from picard.tagger import Tagger


class StreamingAlbum(Album):
    tagger: Tagger | None = None

    def __init__(self, album_id: str):
        """album id should be the actual id from streaming"""
        super().__init__(album_id)

    def _release_request_finished(self, document, http, error):
        pass
        # if self.load_task is None:
        #     return
        # self.load_task = None
        # parse_result = None
        # try:
        #     if error:
        #         self.error_append(http.errorString())
        #         # Fix for broken NAT releases
        #         if error == QtNetwork.QNetworkReply.NetworkError.ContentNotFoundError:
        #             config = get_config()
        #             nats = False
        #             nat_name = config.setting['nat_name']
        #             files = list(self.unmatched_files.files)
        #             for file in files:
        #                 recordingid = file.metadata['musicbrainz_recordingid']
        #                 if mbid_validate(recordingid) and file.metadata['album'] == nat_name:
        #                     nats = True
        #                     self.tagger.move_file_to_nat(file, recordingid)
        #                     self.tagger.nats.update()
        #             if nats and not self.get_num_unmatched_files():
        #                 self.tagger.remove_album(self)
        #                 error = False
        #     else:
        #         try:
        #             parse_result = self._parse_release(document)
        #             config = get_config()
        #             if parse_result == ParseResult.MISSING_TRACK_RELS:
        #                 log.debug("Recording relationships not loaded in initial request for %r, issuing separate requests", self)
        #                 self._request_recording_relationships()
        #             elif parse_result == ParseResult.PARSED:
        #                 self._run_album_metadata_processors()
        #             elif parse_result == ParseResult.REDIRECT:
        #                 error = False
        #         except Exception:
        #             error = True
        #             self.error_append(traceback.format_exc())
        # finally:
        #     self._requests -= 1
        #     if parse_result == ParseResult.PARSED or error:
        #         self._finalize_loading(error)

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
