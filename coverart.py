from picard.i18n import N_
from picard.plugin3.api import (
    CoverArtImage,
    CoverArtProvider,
)

from .api_helpers import get_api_helper_for_provider
from .providers import (
    MetadataProvider,
    Provider,
)


class StreamingCoverArtProvider(CoverArtProvider):
    """Abstract cover art provider for streaming metadata."""

    NAME = "Streaming Cover Art"
    TITLE = N_("Streaming Cover Art")
    provider = Provider.DEEZER

    def queue_images(self):
        provider_attr = getattr(self.album, "metastreaming_provider", None)
        if provider_attr and isinstance(provider_attr, MetadataProvider):
            provider_enum = provider_attr.provider
        else:
            provider_enum = self.provider

        item_id = self.metadata.get(f"{provider_enum.value}_albumid") or self.metadata.get("deezer_albumid")
        if not item_id:
            return CoverArtProvider.QueueState.FINISHED

        cover_size = getattr(self, "api", None) and self.api.plugin_config["cover_size"] or "xl"
        webservice = self.api.web_service if getattr(self, "api", None) else self.album.tagger.webservice
        api_helper = get_api_helper_for_provider(provider_enum, webservice)
        cover_url = api_helper.get_album_cover_url(str(item_id), size=cover_size)

        self.queue_put(CoverArtImage(cover_url, types=["front"]))
        return CoverArtProvider.QueueState.FINISHED


class DeezerCoverArtProvider(StreamingCoverArtProvider):
    NAME = "Deezer Cover Art"
    TITLE = N_("Deezer")
    provider = Provider.DEEZER
