import json
import urllib.request
import sys


def get_json_by_url(url: str):
    try:
        response = urllib.request.urlopen(url=url).read()
        data = json.loads(response)
    except urllib.error.URLError as e:
        print("Error occurred while fetching resource")
        print("Reason: ", e.reason)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax: ", e)
        sys.exit(1)
    except:
        print("Unknown error occurred")
        sys.exit(1)
    return data
