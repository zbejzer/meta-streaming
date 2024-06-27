import os
import sys
import validators

from metastreaming.tagger import tag_file
from metastreaming.url_helpers import parse_deezer_url, deezer_api_url
from metastreaming.web_helper import get_json_by_url


def main():
    try:
        path = input("Enter path to the folder: ")
        deezer_url = input("Enter Deezer URL: ")
    except:
        print("Input error")
        sys.exit(1)

    if not os.path.exists(path):
        print("Given folder doesn't exists!")
        sys.exit(1)
    if not validators.url(deezer_url):
        print("Invalid URL!")
        sys.exit(1)

    deezer_url = parse_deezer_url(deezer_url)
    album = get_json_by_url(deezer_api_url("album", deezer_url["id"]))

    print("Title of the provided album: " + album["title"])
    try:
        confirm = input("Do you want to continue? [Y/n] ")
        if not (confirm == "" or confirm.lower == "y"):
            raise
    except:
        print("Canceled by user")
        sys.exit(1)

    tracks = get_json_by_url(deezer_api_url("album", album["id"], "/tracks"))

    for file in os.scandir(path):
        if file.is_file() and file.name.endswith(".flac"):
            tag_file(album, tracks, file)
