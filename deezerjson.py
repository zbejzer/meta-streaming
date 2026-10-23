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

from .api_helpers import DeezerAPIHelper
from .providers import MetadataProvider


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
        if not isinstance(c, dict) or "name" not in c:
            continue
        item = dict()
        item["name"] = c["name"]

        if i + 2 == len(node):
            item["joinphrase"] = " & "
        elif i + 1 < len(node):
            item["joinphrase"] = ", "
        else:
            item["joinphrase"] = ""

        artist = dict()
        artist["name"] = artist["sort-name"] = c["name"]
        artist["disambiguation"] = ""
        artist["id"] = str(provider.generate_artist_UUID(str(c.get("id", c["name"]))))
        item["artist"] = artist
        ac.append(item)
    return ac


def _mb_track_from_track(node: dict, provider: MetadataProvider):
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

    if node.get("explicit_lyrics"):
        track["explicit"] = True

    return track


def album_to_mb_release(node: dict, provider: MetadataProvider):
    """Create MusicBrainzAPI 'release' node from a Deezer JSON 'album' node."""
    mb_node: dict = dict()
    mb_node["id"] = str(provider.generate_release_UUID())
    mb_node["asin"] = None
    mb_node["status"] = "Official"

    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUM_TO_MB_RELEASE:
            mb_node[_ALBUM_TO_MB_RELEASE[key]] = value

    contributors = node.get("contributors") or node.get("artist") or []
    mb_node["artist-credit"] = _artist_credit_from_contributors(contributors, provider)

    if label_name := node.get("label"):
        mb_node["label-info"] = [
            {
                "catalog-number": None,
                "label": {
                    "name": label_name,
                    "sort-name": label_name,
                    "id": str(provider.generate_label_UUID(label_name)),
                },
            }
        ]
    else:
        mb_node["label-info"] = []

    # Map genres if present
    genres_data = []
    if "genres" in node and isinstance(node["genres"], dict):
        for g in node["genres"].get("data", []):
            if isinstance(g, dict) and "name" in g:
                genres_data.append({"name": g["name"], "count": 1})
    if genres_data:
        mb_node["genres"] = genres_data

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
    _METASTREAMING_ATTRIBUTES: list[str] = [
        "metastreaming_provider",
        "metastreaming_mb_node",
        "metastreaming_tracklist",
    ]

    for i in _METASTREAMING_ATTRIBUTES:
        if hasattr(album, i):
            delattr(album, i)


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
                    album._run_album_metadata_processors()
                elif parse_result == ParseResult.REDIRECT:
                    error = False
            except Exception:
                error = True
                album.error_append(traceback.format_exc())
    finally:
        if parse_result == ParseResult.PARSED or error:
            album._finalize_loading(error)


def _request_track(album: Album, track_id: str) -> None:
    api = PluginApi.get_api()
    deezer_api = DeezerAPIHelper(api.web_service)
    task_id = f"deezer_track_{track_id}"

    def create_request():
        album._load_request = deezer_api.get_track_by_id(
            track_id,
            partial(_track_request_finished, album, task_id),
        )
        return album._load_request

    api.add_album_task(
        album,
        task_id,
        f"Track metadata for {track_id}",
        request_factory=create_request,
        blocking=True,
    )


def _track_request_finished(album: Album, task_id: str, document, http, error) -> None:
    api = PluginApi.get_api()
    api.complete_album_task(album, task_id)
    assert (
        isinstance(album, Album)
        and hasattr(album, "metastreaming_provider")
        and hasattr(album, "metastreaming_mb_node")
    )

    if error:
        _clean_attributes(album)
        _finish_deezer_release(album, None, http, error)
        return

    track_index: int = int(document.get("track_position", 1)) - 1
    disk_index: int = int(document.get("disk_number", 1)) - 1
    mb_track = _mb_track_from_track(document, album.metastreaming_provider)

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
        _clean_attributes(album)
        _finish_deezer_release(album, mb_document, http, error)


def recordings_request_finished_proxy(album: Album, task_id: str, document, http, error) -> None:
    """Handle Deezer album response and queue track requests concurrently."""
    api = PluginApi.get_api()
    api.complete_album_task(album, task_id)
    if error:
        _clean_attributes(album)
        _finish_deezer_release(album, None, http, error)
        return

    assert isinstance(album, Album) and hasattr(album, "metastreaming_provider")
    album.metastreaming_mb_node = album_to_mb_release(cast(dict, document), album.metastreaming_provider)  # type: ignore[attr-defined]

    track_items = document.get("tracks", {}).get("data", [])
    if track_items:
        log.debug("Dispatching %d track requests concurrently for %r", len(track_items), album)
        for track_node in track_items:
            track_id = str(track_node["id"])
            _request_track(album, track_id)
    else:
        mb_node = album.metastreaming_mb_node
        _clean_attributes(album)
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
