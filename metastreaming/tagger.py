import json
import os
from pprint import pprint
import re
import urllib.request
from mutagen.flac import FLAC

from metastreaming.url_helpers import deezer_api_url, parse_deezer_url


def apply_track_tags(album_metadata, track_metadata, file: os.DirEntry):
    ALBUM_TAGS = {
        "title": "ALBUM",
        "upc": "UPC",
        "label": "LABEL",
    }

    TRACK_TAGS = {
        "title": "TITLE",
        "isrc": "ISRC",
        "release_date": "DATE",
        "bpm": "BPM",
    }

    audio = FLAC(filename=file.path)

    # Album contributors
    if "contributors" in album_metadata and len(album_metadata["contributors"]) > 0:
        contributors_list = list()
        for contributor in album_metadata["contributors"]:
            contributors_list.append(contributor["name"])
        audio["ALBUMARTIST"] = contributors_list

    # Track contributors
    if "contributors" in track_metadata and len(track_metadata["contributors"]) > 0:
        contributors_list = list()
        for contributor in track_metadata["contributors"]:
            contributors_list.append(contributor["name"])
        audio["ARTIST"] = contributors_list

    for tag in ALBUM_TAGS:
        if tag in album_metadata:
            audio[ALBUM_TAGS[tag]] = str(album_metadata[tag])
    for tag in TRACK_TAGS:
        if tag in track_metadata:
            audio[TRACK_TAGS[tag]] = str(track_metadata[tag])
    audio.save()


def tag_file(album_metadata, file: os.DirEntry):
    id = int(re.search("^\\d+(?= - )", file.name)[0]) - 1
    print("Processing file: " + file.name)
    track_info = parse_deezer_url(album_metadata["tracks"]["data"][id]["link"])
    track_metadata = json.loads(
        urllib.request.urlopen(url=deezer_api_url("track", track_info["id"])).read()
    )
    apply_track_tags(album_metadata, track_metadata, file)
