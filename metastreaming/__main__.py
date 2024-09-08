import os
import sys
import validators
import argparse

# from metastreaming.tagger import tag_file
from metastreaming.web_helpers import DeezerWebHelper


def main():
    parser = argparse.ArgumentParser(
        prog="metastreaming",
        description="Simple software for obtaining metadata from streaming services and applying them to files",
    )
    parser.add_argument("url")
    parser.add_argument("-d", "--directory", help="set directory with files to tag")
    args = parser.parse_args()

    if args.directory is not None and not os.path.exists(args.directory):
        raise FileNotFoundError(args.directory + " does not exist!")

    if not validators.url(args.url):
        raise ValueError(args.url + " is not a valid URL address!")

    web_helper = DeezerWebHelper()
    web_helper.get_data(args.url)

    print("Title of the provided album / track: " + web_helper.data.title)
    try:
        confirm = input("Do you want to continue? [Y/n] ")
        if not (confirm == "" or confirm.lower == "y"):
            raise
    except:
        print("Canceled by user")
        sys.exit(1)

    web_helper.data.print()

    # tracks = get_json_by_url(deezer_api_url("album", album["id"], "/tracks"))

    # for file in os.scandir(path):
    #     if file.is_file() and file.name.endswith(".flac"):
    #         tag_file(album, tracks, file)


if __name__ == "__main__":
    main()
