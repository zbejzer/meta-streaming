from picard import log
from picard.album import AlbumStatus
from picard.config import get_config
from picard.metadata import Metadata


def load_from_deezer(self, priority=False, refresh=False):
    # if self._requests:
    #     log.info("Not reloading, some requests are still active.")
    #     return
    # self.tagger.window.set_statusbar_message(
    #     N_("Loading album %(id)s …"),
    #     {'id': self.id}
    # )
    # self.loaded = False
    # self.status = AlbumStatus.LOADING
    # if self.release_group:
    #     self.release_group.loaded = False
    #     self.release_group.genres.clear()
    # self.metadata.clear()
    # self.genres.clear()
    # self.update(update_selection=False)
    # self._new_metadata = Metadata()
    # self._new_tracks = []
    # self._requests = 1
    # self.clear_errors()
    # config = get_config()
    # require_authentication = False
    # inc = {
    #     'aliases',
    #     'annotation',
    #     'artist-credits',
    #     'artists',
    #     'collections',
    #     'discids',
    #     'isrcs',
    #     'labels',
    #     'media',
    #     'recordings',
    #     'release-groups',
    # }
    # if self.tagger.webservice.oauth_manager.is_authorized():
    #     require_authentication = True
    #     inc |= {'user-collections'}
    # if config.setting['release_ars'] or config.setting['track_ars']:
    #     inc |= {
    #         'artist-rels',
    #         'recording-rels',
    #         'release-group-level-rels',
    #         'release-rels',
    #         'series-rels',
    #         'url-rels',
    #         'work-rels',
    #     }
    #     if config.setting['track_ars']:
    #         inc |= {
    #             'recording-level-rels',
    #             'work-level-rels',
    #         }
    # require_authentication = self.set_genre_inc_params(inc, config) or require_authentication
    # if config.setting['enable_ratings']:
    #     require_authentication = True
    #     inc |= {'user-ratings'}

    # self.load_task = self.tagger.mb_api.get_release_by_id(
    #     self.id,
    #     self._release_request_finished,
    #     inc=inc,
    #     mblogin=require_authentication,
    #     priority=priority,
    #     refresh=refresh
    # )
    return
