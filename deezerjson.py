from picard.config import get_config
from picard.mbjson import _node_skip_empty_iter
from picard.metadata import Metadata

_ALBUM_TO_METADATA = {"title": "album", "nb_tracks": "tracks"}


def albumsearch_to_metadata(node, m: Metadata, album=None):
    """Make metadata dict from a JSON 'album' node returned by search."""
    config = get_config()
    m.add_unique("deezer_albumid", node["id"])
    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUM_TO_METADATA:
            m[_ALBUM_TO_METADATA[key]] = value
        elif key == "artist":
            m["deezer_albumartistid"] = value["id"]
            m["albumartist"] = value["name"]
