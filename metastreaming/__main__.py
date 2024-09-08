import os
import sys
import validators
import argparse

# from metastreaming.tagger import tag_file
from metastreaming.tagger import tag_files
from metastreaming.web_helpers import DeezerWebHelper


def confirm_prompt(question: str) -> bool:
    prompt = f"{question} [Y/n]: "
    answer = input(prompt).strip().lower()

    if answer in ["y", "yes", ""]:
        return True

    if answer in ["n", "no"]:
        return False

    print(f"{answer} is not a valid choice, please select y/n")
    return confirm_prompt(question)


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
        if not confirm_prompt("Do you want to continue?"):
            raise
    except:
        print("Canceled by user")
        sys.exit(1)

    web_helper.data.print()

    if args.directory is not None:
        tag_files(web_helper.data, args.directory)


if __name__ == "__main__":
    main()
