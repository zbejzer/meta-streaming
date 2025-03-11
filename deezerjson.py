from picard import log
from picard.config import get_config
from picard.dataobj import DataObject
from picard.mbjson import _node_skip_empty_iter
from picard.metadata import Metadata

_ALBUMSEARCH_TO_METADATA: dict[str, str] = {"title": "album", "nb_tracks": "tracks"}

_ALBUM_TO_METADATA = {
    'upc': 'barcode',
    'label': 'label',
    'release_date': 'date',
    'title': 'album',
    'record_type': 'releasetype'
}


def add_genres_from_node(node, obj: DataObject):
    try:
        for tag in node["genres"]["data"]:
            obj.add_genre(tag['name'], 2)   # idk what count actually means, best I could find is it's an upvote count
    except Exception as e:
        log.error("Error adding genres from node: %s", e)


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


def album_to_metadata(node, m: Metadata, album=None):
    """Make metadata dict from a Deezer JSON 'album' node."""
    config = get_config()
    m.add_unique('deezer_albumid', node['id'])
    for key, value in _node_skip_empty_iter(node):
        if key in _ALBUM_TO_METADATA:
            m[_ALBUM_TO_METADATA[key]] = value
        elif key == 'contributors':
            artist_credit_to_metadata(value, m, release=True)
            # set tags from artists
            if album is not None:
                for credit in value:
                    artist = credit['artist']
                    album.append_album_artist(artist['id'])
        elif key == 'relations' and config.setting['release_ars']:
            _relations_to_metadata(value, m, config=config, entity='release')
        elif key == 'label-info':
            m['label'], m['catalognumber'] = label_info_from_node(value)
        elif key == 'text-representation':
            if 'language' in value:
                m['~releaselanguage'] = value['language']
            if 'script' in value:
                m['script'] = value['script']
    m['~releasecountries'] = release_countries = countries_from_node(node)
    # The MB web service returns the first release country in the country tag.
    # If the user has configured preferred release countries, use the first one
    # if it is one in the complete list of release countries.
    for country in config.setting['preferred_release_countries']:
        if country in release_countries:
            m['releasecountry'] = country
            break
    add_genres_from_node(node, album)
