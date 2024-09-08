import os
import sys
from mutagen.flac import FLAC
from mutagen import MutagenError

from metastreaming.album import Album


def tag_files(item: Album, path: str) -> None:
    ALBUM_TAGS = {
        "title": "ALBUM",
        "upc": "UPC",
        "label": "LABEL",
        "release_date": "DATE",
    }

    TRACK_TAGS = {
        "title": "TITLE",
        "isrc": "ISRC",
        "release_date": "DATE",
        "bpm": "BPM",
        "gain": "TRACK_GAIN",
    }

    for file in os.scandir(path):
        if file.is_file() and file.name.endswith(".flac"):
            print("Processing file: " + file.name)
            audio = FLAC(filename=file.path)
            disk_number = int(audio["DISCNUMBER"][0])
            track_number = int(audio["TRACKNUMBER"][0])
            track_index = 0

            for i in range(0, len(item.tracks)):
                if int(item.tracks[i].track_number) == track_number and (
                    disk_number == None
                    or int(item.tracks[i].disc_number) == disk_number
                ):
                    track_index = i
                    break

            # Album contributors
            if item.artist != None:
                audio["ALBUMARTIST"] = item.artist

            # Track contributors
            if item.tracks[track_index].artist != None:
                audio["ARTIST"] = item.tracks[track_index].artist

            for tag in ALBUM_TAGS:
                metadata = getattr(item, tag)
                if metadata != None:
                    audio[ALBUM_TAGS[tag]] = str(metadata)
            for tag in TRACK_TAGS:
                metadata = getattr(item.tracks[track_index], tag)
                if metadata != None:
                    audio[TRACK_TAGS[tag]] = str(metadata)
            try:
                audio.save()
            except MutagenError as e:
                print("Error occurred while saving track")
                print(e)
                sys.exit(1)
