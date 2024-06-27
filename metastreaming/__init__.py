import json
import os
import re
import urllib.request
import sys
import validators

from metastreaming.tagger import tag_file
from metastreaming.url_helpers import parse_deezer_url, deezer_api_url


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

    try:
        response = urllib.request.urlopen(
            url=deezer_api_url("album", deezer_url["id"])
        ).read()
        album = json.loads(response)
    except urllib.error.URLError as e:
        print("Error occurred while fetching album")
        print("Reason: " + e.reason)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax: ", e)
        sys.exit(1)

    print("Title of the provided album: " + album["title"])
    confirm = input("Do you want to continue? [Y/n] ")
    if not (confirm == "" or confirm.lower == "y"):
        print("Canceled by user")
        sys.exit(1)

    for file in os.scandir(path):
        if file.is_file() and file.name.endswith(".flac"):
            if re.search("^\\d+(?= - )", file.name)[0] is not None:
                tag_file(album, file)
