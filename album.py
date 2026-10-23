from functools import partial

from picard import log
from picard.album import AlbumStatus
from picard.i18n import N_
from picard.plugin3.api import (
    Album,
    Metadata,
    PluginApi,
)
from picard.tagger import Tagger

from . import deezerjson


# Dynamically added to Album class
def load_from_deezer(self, priority=False, refresh=False):
    assert isinstance(self, Album)
    assert isinstance(self.tagger, Tagger)  # pyright: ignore[reportAttributeAccessIssue]
    if self.has_critical_tasks():
        log.info("Not reloading, some requests are still active.")
        return
    self.tagger.window.set_statusbar_message(N_("Loading album %(id)s …"), {"id": self.id})
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
    self._pending_tasks.clear()
    self.clear_errors()

    api = PluginApi.get_api()
    task_id = f"deezer_release_{self.id}"

    def create_request():
        self._load_request = self.tagger.deezer_api.get_release_by_id(  # pyright: ignore[reportAttributeAccessIssue]
            self.metastreaming_provider.actual_id,  # pyright: ignore[reportAttributeAccessIssue]
            partial(deezerjson.recordings_request_finished_proxy, self, task_id),
            priority=priority,
            refresh=refresh,
        )
        return self._load_request

    api.add_album_task(
        self,
        task_id,
        f"Release metadata for {self.id}",
        request_factory=create_request,
        blocking=True,
    )
