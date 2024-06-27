import re

DEEZER_API_URL = "https://api.deezer.com"


def parse_deezer_url(url):
    """Extract language, resource type and id from a Deezer URL.
    Returns a dict with resource and id keys on success, None otherwise
    """
    r = re.compile(
        r"^https?://(?:www.)?deezer.com(?:/(?P<language>.+))?/(?P<service>[A-Za-z]+)/(?P<id>[A-Za-z0-9]+)"
    )
    match = r.match(url)
    if match is not None:
        return match.groupdict()
    return None


def deezer_api_url(service, id):
    # https://api.deezer.com/version/service/id/method/?parameters
    return "{}/{}/{}".format(DEEZER_API_URL, service, id)
