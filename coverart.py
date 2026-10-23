from picard.i18n import N_
from picard.plugin3.api import (
    CoverArtImage,
    CoverArtProvider,
)

from .api_helpers import get_api_helper_for_provider
from .providers import Provider


class StreamingCoverArtProvider(CoverArtProvider):
    """Abstract cover art provider for streaming metadata."""

    NAME = "Streaming Cover Art"
    TITLE = N_("Streaming Cover Art")
    provider: Provider = Provider.DEEZER

    def queue_images(self):
        item_id = self.metadata.get(f"{self.provider.value}_albumid")
        if not item_id:
            return CoverArtProvider.QueueState.FINISHED

        cover_size = self.api.plugin_config["cover_size"]
        api_helper = get_api_helper_for_provider(self.provider, self.api.web_service)
        cover_url = api_helper.get_album_cover_url(str(item_id), size=cover_size)

        self.queue_put(CoverArtImage(cover_url, types=["front"]))
        return CoverArtProvider.QueueState.FINISHED


class DeezerCoverArtProvider(StreamingCoverArtProvider):
    NAME = "Deezer Cover Art"
    TITLE = N_("Deezer")
    provider = Provider.DEEZER
