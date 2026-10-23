from picard.i18n import N_
from picard.plugin3.api import (
    CoverArtImage,
    CoverArtProvider,
)


class DeezerCoverArtProvider(CoverArtProvider):
    NAME = "Deezer Cover Art"
    TITLE = N_("Deezer")

    def queue_images(self):
        deezer_id = self.metadata.get("deezer_albumid")
        if not deezer_id:
            return CoverArtProvider.QueueState.FINISHED

        cover_size = getattr(self, "api", None) and self.api.plugin_config["cover_size"] or "xl"
        cover_url = f"https://api.deezer.com/album/{deezer_id}/image?size={cover_size}"
        self.queue_put(CoverArtImage(cover_url, types=["front"]))
        return CoverArtProvider.QueueState.FINISHED
