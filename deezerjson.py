from functools import partial
import json
from typing import cast
from picard import log
from picard.album import Album
from picard.config import get_config
from picard.dataobj import DataObject
from picard.mbjson import _node_skip_empty_iter
from picard.metadata import Metadata
from picard.plugins.metastreaming.api_helpers import DeezerAPIHelper
from picard.plugins.metastreaming.providers import MetadataProvider
from picard.tagger import Tagger


_TRACK_TO_MB_TRACK = {
    'id': 'deezer_trackid',
    'title': 'title',
}

_ALBUM_TO_MB_RELEASE = {
    'id': 'deezer_albumid',
    'upc': 'barcode',
    'release_date': 'date',
    'title': 'title',
}

_ALBUMSEARCH_TO_METADATA: dict[str, str] = {"title": "album", "nb_tracks": "tracks"}


def _artist_credit_from_contributors(node: dict, provider: MetadataProvider):
    ac = dict()
    for i, c in enumerate(node):
        ac[i] = dict()
        ac[i]["name"] = c["name"]
        artist = dict()
        artist["name"] = artist["sort-name"] = c["name"]
        artist["disambiguation"] = ""
        artist["id"] = str(provider.generate_artist_UUID(c["id"]))
        ac[i]["artist"] = artist
    return ac


def _track_from_track(node: dict, provider: MetadataProvider):
    # TODO: Add per-track artist credit parsing
    track = dict()

    for key, value in _node_skip_empty_iter(node):
        if key in _TRACK_TO_MB_TRACK:
            track[_TRACK_TO_MB_TRACK[key]] = value

    track["id"] = str(provider.generate_track_UUID(str(node["id"])))
    track["length"] = int(node["duration"]) * 1000
    track["recording"] = dict(track)
    track["position"] = int(node["track_position"])
    track["number"] = str(node["track_position"])
    track["recording"]["isrcs"] = dict()
    track["recording"]["isrcs"][0] = node["isrc"]

    return track


def _media_from_tracklist(node: dict, provider: MetadataProvider):
    media = dict()
    deezer_api = Tagger.instance().deezer_api       # pyright: ignore[reportAttributeAccessIssue]
    assert isinstance(deezer_api, DeezerAPIHelper)

    for i in node:
        track = _track_from_track(i, provider)
        track_index: int = int(track["position"]) - 1
        disk_index: int = int(i["disk_number"]) - 1
        try:
            media[disk_index][track_index] = track
        except KeyError:
            media[disk_index] = dict()
            media[disk_index][track_index] = track

    return media


def album_to_mb_release(node: dict, provider: MetadataProvider):
    """Create MusicBrainzAPI 'release' node from a Deezer JSON 'album' node."""
    mb_node = dict()
    mb_node["id"] = str(provider.generate_release_UUID())
    mb_node["asin"] = None
    mb_node["status"] = "Official"

    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUM_TO_MB_RELEASE:
            mb_node[_ALBUM_TO_MB_RELEASE[key]] = value

    mb_node["artist-credit"] = _artist_credit_from_contributors(node["contributors"], provider)

    mb_node["label-info"] = dict()
    mb_node["label-info"][0] = dict()
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

    # debug_str: str = json.dumps(mb_node)

    return mb_node


def _streaming_tracklist(album, document, http, error):
    try:
        log.debug("Loading recording relationships for %r", album)
        assert isinstance(album, Album)
        try:
            album.metastreaming_mb_node["media"] = _media_from_tracklist(document["data"], album.metastreaming_provider)      # pyright: ignore[reportAttributeAccessIssue]
        except AttributeError as e:
            log.error("Attribute %s not found in %r. Function was probably called directly", e, album)
    finally:
        album._requests -= 1
        # Continue with normal track processing
        return album._release_request_finished(album.metastreaming_mb_node, http, error)    # pyright: ignore[reportAttributeAccessIssue]


def streaming_response_proxy(album, document, http, error):
    """Essentially wrapper around Album._release_request_finished"""
    # TODO: Add error handling
    assert isinstance(album, Album)
    album.metastreaming_mb_node = album_to_mb_release(cast(dict, document), album.metastreaming_provider)         # pyright: ignore[reportAttributeAccessIssue]

    log.debug("Album tracklist not loaded in initial request for %r, issuing separate requests", album)
    priority = False
    refresh = False
    album._requests += 1
    album.load_task = album.tagger.deezer_api.get_tracklist_by_id(  # pyright: ignore[reportAttributeAccessIssue]
        album.metastreaming_provider.actual_id,  # pyright: ignore[reportAttributeAccessIssue]
        partial(_streaming_tracklist, album),
        priority=priority,
        refresh=refresh
    )


def albumsearch_to_metadata(node, m: Metadata, album=None):
    """Make metadata dict from a Deezer JSON 'album' node returned by search."""
    m.add_unique("deezer_albumid", node["id"])
    m["source"] = "Deezer"
    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUMSEARCH_TO_METADATA:
            m[_ALBUMSEARCH_TO_METADATA[key]] = value
        elif key == "artist":
            m["deezer_albumartistid"] = value["id"]
            m["albumartist"] = value["name"]
