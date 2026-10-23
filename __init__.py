# -*- coding: utf-8 -*-
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


from picard.plugin3.api import PluginApi

from picard.plugin3.api import (
    Album,
    BaseAction,
    Cluster,
)

from typing import cast


from .album import load_from_deezer
from .albumsearch import StreamingAlbumSearchDialog
from .api_helpers import DeezerAPIHelper

from PyQt6 import QtCore


class GetMetaStreaming(BaseAction):
    TITLE = "Get metadata from streamings"

    # technically redundant because class inherits after QObject and tagger is added to it dynamically
    # during tagger init, but explicitly creating it can't hurt
    tagger: Tagger | None = None

    def callback(self, objs):
        assert isinstance(self.tagger, Tagger)

        # redundant check for now, but keeping it for the possible future use
        if isinstance(objs[0], Cluster):
            dialog = StreamingAlbumSearchDialog(
                self.tagger.window, force_advanced_search=True
            )
            dialog.show_similar_albums(objs[0])
            dialog.exec()
            return
        else:
            self.api.logger.debug(
                "GetMetaStreaming expected a Cluster, got %r", objs[0]
            )
            return


assert hasattr(QtCore.QObject, "tagger") and isinstance(QtCore.QObject.tagger, Tagger)
GetMetaStreaming.tagger = QtCore.QObject.tagger
_deezer_api: DeezerAPIHelper = DeezerAPIHelper(QtCore.QObject.tagger.webservice)

# FIXME: awful way to do this but I don't care enough to do it better
setattr(Tagger, "deezer_api", _deezer_api)
setattr(Album, "load_from_deezer", load_from_deezer)

# TODO: Implement for albums,tracks, etc.


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.register_cluster_action(GetMetaStreaming)
