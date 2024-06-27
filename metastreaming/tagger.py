import json
import os
import pprint
import sys
import re
import urllib.request
from mutagen.flac import FLAC
from mutagen import MutagenError

from metastreaming.url_helpers import deezer_api_url, parse_deezer_url
from metastreaming.web_helper import get_json_by_url


def apply_track_tags(album_metadata, track_metadata, file: os.DirEntry):
    print("Deezer track name: " + track_metadata["title"])
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
    try:
        audio.save()
    except MutagenError as e:
        print("Error occurred while saving track")
        print(e)
        sys.exit(1)


def tag_file(album_metadata, tracks, file: os.DirEntry):
    print("Processing file: " + file.name)
    audio = FLAC(filename=file.path)
    disk_number = int(audio["DISCNUMBER"][0])
    track_number = int(audio["TRACKNUMBER"][0])
    track_index = track_number - 1

    if not disk_number == None:
        for i in range(0, int(album_metadata["nb_tracks"])):
            if (
                int(tracks["data"][i]["track_position"]) == track_number
                and int(tracks["data"][i]["disk_number"]) == disk_number
            ):
                track_index = i
                break

    track_id = tracks["data"][track_index]["id"]
    track_metadata = get_json_by_url(deezer_api_url("track", track_id))
    apply_track_tags(album_metadata, track_metadata, file)
