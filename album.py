from functools import partial
from typing import cast

from picard import log
from picard.album import AlbumStatus, Album
from picard.config import get_config
from picard.metadata import Metadata
from picard.tagger import Tagger

from picard.plugins.metastreaming import deezerjson


# Dynamically added to Album class
def load_from_deezer(self, priority=False, refresh=False):
    assert isinstance(self, Album)
    assert isinstance(self.tagger, Tagger)  # pyright: ignore[reportAttributeAccessIssue]
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

    self.load_task = self.tagger.deezer_api.get_release_by_id(  # pyright: ignore[reportAttributeAccessIssue]
        self.metastreaming_provider.actual_id,  # pyright: ignore[reportAttributeAccessIssue]
        partial(deezerjson.streaming_response_proxy, self),
        priority=priority,
        refresh=refresh
    )
