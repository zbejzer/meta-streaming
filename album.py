from functools import partial

from picard import log
from picard.album import AlbumStatus
from picard.i18n import N_
from picard.plugin3.api import (
    Album,
    Metadata,
    PluginApi,
)

from . import deezerjson
from .api_helpers import DeezerAPIHelper
from .providers import MetadataProvider


def load_deezer_album(
    api: PluginApi,
    deezer_album_id: str,
    cluster=None,
    priority: bool = False,
    refresh: bool = False,
) -> Album:
    """Load a Deezer album into Picard using synthetic MusicBrainz UUIDs."""
    provider = MetadataProvider(MetadataProvider.Names.DEEZER, str(deezer_album_id))
    release_mbid = str(provider.generate_release_UUID())

    # Register release group
    rg_mbid = str(provider.generate_releasegroup_UUID())
    api.tagger.get_release_group_by_id(rg_mbid).loaded_albums.add(release_mbid)

    album = api.tagger.albums.get(release_mbid)
    if not album:
        album = Album(release_mbid)
        api.tagger.albums[release_mbid] = album
        api.tagger.album_added.emit(album)

    album.metastreaming_provider = provider  # type: ignore[attr-defined]

    if album.has_critical_tasks():
        log.info("Not reloading album %s, some requests are still active.", release_mbid)
        return album

    api.tagger.window.set_statusbar_message(N_("Loading album %(id)s …"), {"id": release_mbid})
    album.loaded = False
    album.status = AlbumStatus.LOADING
    if album.release_group:
        album.release_group.loaded = False
        album.release_group.genres.clear()
    album.metadata.clear()
    album.genres.clear()
    album.update(update_selection=False)
    album._new_metadata = Metadata()
    album._new_tracks = []
    album._pending_tasks.clear()
    album.clear_errors()

    deezer_api = DeezerAPIHelper(api.web_service)
    task_id = f"deezer_release_{release_mbid}"

    def create_request():
        album._load_request = deezer_api.get_release_by_id(
            str(deezer_album_id),
            partial(deezerjson.recordings_request_finished_proxy, album, task_id),
            priority=priority,
            refresh=refresh,
        )
        return album._load_request

    api.add_album_task(
        album,
        task_id,
        f"Release metadata for {release_mbid}",
        request_factory=create_request,
        blocking=True,
    )

    if cluster and cluster.files:
        api.tagger.move_files_to_album(cluster.files, release_mbid, album)

    return album
