from functools import partial
import traceback
from typing import cast

from picard import log
from picard.album import ParseResult
from picard.mbjson import _node_skip_empty_iter
from picard.plugin3.api import (
    Album,
    Metadata,
    PluginApi,
)

from .api_helpers import (
    get_api_helper_for_provider,
)
from .providers import (
    MetadataProvider,
    Provider,
)


_TRACK_TO_MB_TRACK: dict[str, str] = {
    "id": "deezer_trackid",
    "title": "title",
}

_ALBUM_TO_MB_RELEASE: dict[str, str] = {
    "id": "deezer_albumid",
    "upc": "barcode",
    "release_date": "date",
    "title": "title",
}

_ALBUMSEARCH_TO_METADATA: dict[str, str] = {"title": "album", "nb_tracks": "tracks"}


def _artist_credit_from_contributors(node: list | dict, provider: MetadataProvider):
    ac: list = list()
    if isinstance(node, dict):
        node = [node]
    for i, c in enumerate(node):
        try:
            name = c["name"]
        except (KeyError, TypeError):
            continue

        item = {
            "name": name,
            "joinphrase": " & " if i + 2 == len(node) else (", " if i + 1 < len(node) else ""),
            "artist": {
                "name": name,
                "sort-name": name,
                "disambiguation": "",
                "id": str(provider.generate_artist_UUID(str(c.get("id", name)))),
            },
        }
        ac.append(item)
    return ac


def _mb_track_from_track(node: dict, provider: MetadataProvider, api: PluginApi):
    track = dict()

    for key, value in _node_skip_empty_iter(node):
        if key in _TRACK_TO_MB_TRACK:
            track[_TRACK_TO_MB_TRACK[key]] = value

    track["id"] = str(provider.generate_track_UUID(str(node["id"])))
    track["length"] = int(node.get("duration", 0)) * 1000
    track["recording"] = dict(track)
    track["position"] = int(node.get("track_position", 1))
    track["number"] = str(node.get("track_position", 1))

    contributors = node.get("contributors") or node.get("artist") or []
    track["artist-credit"] = _artist_credit_from_contributors(contributors, provider)

    track["recording"]["isrcs"] = list()
    if isrc := node.get("isrc"):
        track["recording"]["isrcs"].append(str(isrc))
    track["recording"]["artist-credit"] = track["artist-credit"]
    track["recording"]["relations"] = list()

    if api.plugin_config["tag_explicit"] and node.get("explicit_lyrics"):
        track["explicit"] = True

    return track


def album_to_mb_release(node: dict, provider: MetadataProvider):
    """Create MusicBrainzAPI 'release' node from a Deezer JSON 'album' node."""
    mb_node: dict = dict()
    mb_node["id"] = str(provider.generate_release_UUID())
    mb_node["status"] = "Official"

    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUM_TO_MB_RELEASE:
            mb_node[_ALBUM_TO_MB_RELEASE[key]] = value

    contributors = node.get("contributors") or node.get("artist") or []
    mb_node["artist-credit"] = _artist_credit_from_contributors(contributors, provider)

    if label_name := node.get("label"):
        # Picard consumes only the label name (label_info_from_node), no
        # musicbrainz_labelid tag exists, so no synthetic label UUID is generated.
        mb_node["label-info"] = [
            {
                "catalog-number": None,
                "label": {
                    "name": label_name,
                    "sort-name": label_name,
                },
            }
        ]
    else:
        mb_node["label-info"] = []

    # Map genres if present
    try:
        mb_node["genres"] = [{"name": g["name"], "count": 1} for g in node["genres"]["data"] if "name" in g]
    except (KeyError, TypeError):
        pass

    record_type = str(node.get("record_type", "album")).capitalize()
    mb_node["release-group"] = {
        "disambiguation": "",
        "id": str(provider.generate_releasegroup_UUID()),
        "artist-credit": mb_node["artist-credit"],
        "title": mb_node.get("title", ""),
        "primary-type": record_type,
    }

    # Prepare for per-track processing
    mb_node["media"] = list()

    return mb_node


def _clean_attributes(album) -> None:
    for attr in ("metastreaming_provider", "metastreaming_mb_node"):
        try:
            delattr(album, attr)
        except AttributeError:
            pass


def _finish_deezer_release(album: Album, mb_document: dict | None, http, error) -> None:
    album._load_request = None
    parse_result = None
    try:
        if error:
            album.error_append(http.errorString())
        else:
            try:
                parse_result = album._parse_release(mb_document)
                if parse_result == ParseResult.PARSED:
                    provider_attr = getattr(album, "metastreaming_provider", None)
                    if provider_attr:
                        album._new_metadata[f"{provider_attr.provider.value}_albumid"] = provider_attr.actual_id
                    album._run_album_metadata_processors()
                elif parse_result == ParseResult.REDIRECT:
                    error = False
            except Exception:
                error = True
                album.error_append(traceback.format_exc())
    finally:
        _clean_attributes(album)
        if parse_result == ParseResult.PARSED or error:
            album._finalize_loading(error)


def _request_track(api: PluginApi, album: Album, track_id: str) -> None:
    provider_attr = getattr(album, "metastreaming_provider", None)
    provider_enum = provider_attr.provider if provider_attr else Provider.DEEZER
    api_helper = get_api_helper_for_provider(provider_enum, api.web_service)
    task_id = f"{provider_enum.value}_track_{track_id}"

    def create_request():
        album._load_request = api_helper.get_track_by_id(
            track_id,
            partial(_track_request_finished, api, album, task_id),
        )
        return album._load_request

    api.add_album_task(
        album,
        task_id,
        f"Track metadata for {track_id}",
        request_factory=create_request,
        blocking=True,
    )


def _track_request_finished(api: PluginApi, album: Album, task_id: str, document, http, error) -> None:
    api.complete_album_task(album, task_id)

    if error or not hasattr(album, "metastreaming_mb_node"):
        album.cancel_tasks()
        _finish_deezer_release(album, None, http, error)
        return

    track_index: int = int(document.get("track_position", 1)) - 1
    disk_index: int = int(document.get("disk_number", 1)) - 1
    mb_track = _mb_track_from_track(document, album.metastreaming_provider, api)

    while len(album.metastreaming_mb_node["media"]) < disk_index + 1:
        medium_pos = len(album.metastreaming_mb_node["media"]) + 1
        album.metastreaming_mb_node["media"].append(
            {
                "position": medium_pos,
                "format": "Digital Media",
                "track-count": 0,
                "tracks": list(),
            }
        )

    while len(album.metastreaming_mb_node["media"][disk_index]["tracks"]) < track_index + 1:
        album.metastreaming_mb_node["media"][disk_index]["tracks"].append(dict())

    album.metastreaming_mb_node["media"][disk_index]["tracks"][track_index] = mb_track
    album.metastreaming_mb_node["media"][disk_index]["track-count"] = len(
        album.metastreaming_mb_node["media"][disk_index]["tracks"]
    )

    # When all parallel track tasks finish, finalize the release
    if not album.has_critical_tasks():
        mb_document = album.metastreaming_mb_node
        _finish_deezer_release(album, mb_document, http, error)


def recordings_request_finished_proxy(api: PluginApi, album: Album, task_id: str, document, http, error) -> None:
    """Handle Deezer album response and queue track requests concurrently."""
    api.complete_album_task(album, task_id)
    if error:
        _finish_deezer_release(album, None, http, error)
        return

    provider_attr = getattr(album, "metastreaming_provider", None)
    if not provider_attr:
        _finish_deezer_release(album, None, http, error)
        return

    album.metastreaming_mb_node = album_to_mb_release(cast(dict, document), provider_attr)

    track_items = document.get("tracks", {}).get("data", [])
    if track_items:
        log.debug("Dispatching %d track requests concurrently for %r", len(track_items), album)
        for track_node in track_items:
            track_id = str(track_node["id"])
            _request_track(api, album, track_id)
    else:
        mb_node = album.metastreaming_mb_node
        _finish_deezer_release(album, mb_node, http, error)


def albumsearch_to_metadata(node, m: Metadata, album=None) -> None:
    """Make metadata dict from a Deezer JSON 'album' node returned by search."""
    m.add_unique("deezer_albumid", node["id"])
    m["source"] = "Deezer"
    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUMSEARCH_TO_METADATA:
            m[_ALBUMSEARCH_TO_METADATA[key]] = value
        elif key == "artist":
            m["deezer_albumartistid"] = value["id"]
            m["albumartist"] = value["name"]
