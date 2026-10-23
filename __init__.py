# MetaStreaming plugin for Picard
#
# Copyright (C) 2025 Stanisław Borodziuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
#
# Changelog:
# [2023-06-17] Initial version
# [2025-01-21] Complete rework
# [2026-10-23] Started working on API V3 migration


from PyQt6 import QtCore

from picard.plugin3.api import (
    Album,
    BaseAction,
    Cluster,
    PluginApi,
)
from picard.tagger import Tagger
from picard.webservice import ratecontrol

from .album import load_from_deezer
from .albumsearch import StreamingAlbumSearchDialog
from .api_helpers import DeezerAPIHelper
from .coverart import DeezerCoverArtProvider


class GetMetaStreaming(BaseAction):
    TITLE = "Get metadata from streamings"

    def callback(self, objs):
        if objs and isinstance(objs[0], Cluster):
            dialog = StreamingAlbumSearchDialog(
                self.api.tagger.window,
                force_advanced_search=True,
            )
            dialog.show_similar_albums(objs[0])
            dialog.exec()
        else:
            self.api.logger.debug(
                "GetMetaStreaming expected a Cluster, got %r",
                objs[0] if objs else None,
            )


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.plugin_config.register_option(
        "rate_limit_ms",
        100,
        title="Deezer API minimum request delay (ms)",
        in_profile=True,
        bounds=(50, 2000),
    )
    delay_ms = api.plugin_config["rate_limit_ms"]
    ratecontrol.set_minimum_delay_for_url("https://api.deezer.com", delay_ms)

    api.plugin_persist.register_option(
        StreamingAlbumSearchDialog.dialog_header_state,
        QtCore.QByteArray(),
    )
    deezer_api = DeezerAPIHelper(api.web_service)
    Tagger.deezer_api = deezer_api  # type: ignore[attr-defined]
    if api.tagger is not None:
        api.tagger.deezer_api = deezer_api  # type: ignore[attr-defined]
    Album.load_from_deezer = load_from_deezer  # type: ignore[attr-defined]
    api.register_cluster_action(GetMetaStreaming)
    api.register_cover_art_provider(DeezerCoverArtProvider)


def disable():
    """Called when plugin is disabled."""
    if hasattr(Tagger, "deezer_api"):
        delattr(Tagger, "deezer_api")
    if hasattr(Album, "load_from_deezer"):
        delattr(Album, "load_from_deezer")
