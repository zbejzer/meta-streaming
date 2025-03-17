from collections import deque
from functools import partial
from lib2to3.pgen2.literals import evalString
from typing import Deque, cast

from picard import log
from picard.album import Album
from picard.mbjson import _node_skip_empty_iter
from picard.metadata import Metadata

from picard.plugins.metastreaming.api_helpers import DeezerAPIHelper
from picard.plugins.metastreaming.providers import MetadataProvider

_TRACK_TO_MB_TRACK: dict[str, str] = {
    'id': 'deezer_trackid',
    'title': 'title',
}

_ALBUM_TO_MB_RELEASE: dict[str, str] = {
    'id': 'deezer_albumid',
    'upc': 'barcode',
    'release_date': 'date',
    'title': 'title',
}

_ALBUMSEARCH_TO_METADATA: dict[str, str] = {
    "title": "album",
    "nb_tracks": "tracks"
}


def _artist_credit_from_contributors(node: dict, provider: MetadataProvider):
    ac: list = list()
    for i, c in enumerate(node):
        ac.append(dict())
        ac[i]["name"] = c["name"]

        if i + 2 == len(node):
            ac[i]["joinphrase"] = " & "
        elif i + 1 < len(node):
            ac[i]["joinphrase"] = ", "
        else:
            ac[i]["joinphrase"] = ""

        artist = dict()
        artist["name"] = artist["sort-name"] = c["name"]
        artist["disambiguation"] = ""
        artist["id"] = str(provider.generate_artist_UUID(c["id"]))
        ac[i]["artist"] = artist
    return ac


def _mb_track_from_track(node: dict, provider: MetadataProvider):
    track = dict()

    for key, value in _node_skip_empty_iter(node):
        if key in _TRACK_TO_MB_TRACK:
            track[_TRACK_TO_MB_TRACK[key]] = value

    track["id"] = str(provider.generate_track_UUID(str(node["id"])))
    track["length"] = int(node["duration"]) * 1000
    track["recording"] = dict(track)
    track["position"] = int(node["track_position"])
    track["number"] = str(node["track_position"])
    track["artist-credit"] = _artist_credit_from_contributors(node["contributors"], provider)

    track["recording"]["isrcs"] = list()
    track["recording"]["isrcs"].append(str(node["isrc"]))
    track["recording"]["artist-credit"] = track["artist-credit"]

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

    mb_node["artist-credit"] = _artist_credit_from_contributors(node["contributors"], provider)

    mb_node["label-info"] = list()
    mb_node["label-info"].append(dict())
    mb_node["label-info"][0]["catalog-number"] = None
    label_mb = dict()
    label_mb["name"] = label_mb["sort-name"] = node["label"]
    label_mb["id"] = str(provider.generate_label_UUID())
    mb_node["label-info"][0]["label"] = label_mb

    mb_node["release-group"] = dict()
    mb_node["release-group"]["disambiguation"] = ""
    mb_node["release-group"]["id"] = str(provider.generate_releasegroup_UUID())
    mb_node["release-group"]["artist-credit"] = mb_node["artist-credit"]
    mb_node["release-group"]["title"] = mb_node["title"]
    mb_node["release-group"]["primary-type"] = node["record_type"]

    # Prepare for later per-track processing
    mb_node["media"] = list()

    return mb_node


def _clean_attributes(album) -> None:
    _METASTREAMING_ATTRIBUTES: list[str] = [
        "metastreaming_provider",
        "metastreaming_mb_node",
        "metastreaming_tracklist"
    ]

    for i in _METASTREAMING_ATTRIBUTES:
        if hasattr(album, i):
            delattr(album, i)


def _request_track(album, id) -> None:
    log.debug("Album tracks not loaded in initial request for %r, issuing separate requests", album)
    album._requests += 1
    assert isinstance(album.tagger.deezer_api, DeezerAPIHelper)
    album.load_task = album.tagger.deezer_api.get_track_by_id(
        id,
        partial(_track_request_finished, album),
    )


def _track_request_finished(album, document, http, error) -> None:
    assert isinstance(album, Album) and \
        hasattr(album, "metastreaming_provider") and \
        hasattr(album, "metastreaming_mb_node") and \
        hasattr(album, "metastreaming_tracklist") and \
        isinstance(album.metastreaming_tracklist, Deque)

    if error:
        album.error_append(http.errorString())
        album._requests -= 1
        _clean_attributes(album)
        album._finalize_loading(error)
        return

    track_index: int = int(document["track_position"]) - 1
    disk_index: int = int(document["disk_number"]) - 1
    mb_track = _mb_track_from_track(document, album.metastreaming_provider)

    while len(album.metastreaming_mb_node["media"]) < disk_index + 1:
        album.metastreaming_mb_node["media"].append({"tracks": list()})

    while len(album.metastreaming_mb_node["media"][disk_index]["tracks"]) < track_index + 1:
        album.metastreaming_mb_node["media"][disk_index]["tracks"].append(dict())

    album.metastreaming_mb_node["media"][disk_index]["tracks"][track_index] = mb_track

    if len(album.metastreaming_tracklist) > 0:
        album._requests -= 1
        next_track_id = album.metastreaming_tracklist.popleft()
        _request_track(album, next_track_id)
    else:
        album._requests -= 1
        mb_document = album.metastreaming_mb_node
        _clean_attributes(album)
        album._release_request_finished(mb_document, http, error)


def recordings_request_finished_proxy(album, document, http, error) -> None:
    """Essentially wrapper around Album._release_request_finished"""
    if error:
        album.error_append(http.errorString())
        album._requests -= 1
        _clean_attributes(album)
        album._finalize_loading(error)
        return

    assert isinstance(album, Album) and hasattr(album, "metastreaming_provider")
    album.metastreaming_mb_node = album_to_mb_release(cast(dict, document), album.metastreaming_provider)   # type: ignore[attr-defined]
    album.metastreaming_tracklist = deque()                                                                 # type: ignore[attr-defined]
    assert hasattr(album, "metastreaming_mb_node") and hasattr(album, "metastreaming_tracklist")

    for track in document["tracks"]["data"]:
        album.metastreaming_tracklist.append(str(track["id"]))

    if len(album.metastreaming_tracklist) > 0:
        track_id = album.metastreaming_tracklist.popleft()
        _request_track(album, track_id)
    else:
        mb_node = album.metastreaming_mb_node
        _clean_attributes(album)
        return album._release_request_finished(mb_node, http, error)


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
