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


from typing import cast

from PyQt5 import QtCore

from picard.plugins.metastreaming.api_helpers import DeezerAPIHelper
from picard.tagger import Tagger
from picard.ui.itemviews import BaseAction, register_cluster_action
from picard.cluster import Cluster
from picard.album import Album
from picard import log

from picard.plugins.metastreaming.albumsearch import StreamingAlbumSearchDialog
from picard.plugins.metastreaming.album import StreamingAlbum

PLUGIN_NAME = "Streaming Metadata"
PLUGIN_AUTHOR = "Stanisław Borodziuk"
PLUGIN_DESCRIPTION = "Get metadata from streaming services"
PLUGIN_VERSION = "0.3.1"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"


class GetMetaStreaming(BaseAction):
    NAME = "Get metadata from streamings"

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
            dialog.exec_()
            return
        else:
            log.debug("GetMetaStreaming expected a Cluster, got %r", objs[0])
            return


GetMetaStreaming.tagger = cast(Tagger, QtCore.QObject.tagger)
StreamingAlbum.tagger = cast(Tagger, QtCore.QObject.tagger)

_deezer_api: DeezerAPIHelper = DeezerAPIHelper(QtCore.QObject.tagger.webservice)

# FIXME: awful way to do this but I don't care enough to do it better
setattr(Tagger, 'deezer_api', _deezer_api)

# TODO: Implement for albums,tracks, etc.
register_cluster_action(GetMetaStreaming())
