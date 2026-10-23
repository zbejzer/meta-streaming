from typing import ClassVar

from PyQt6 import QtWidgets

from picard.i18n import (
    N_,
    gettext as _,
)
from picard.plugin3.api import (
    OptionsPage,
    PageOptionConfigs,
)
from picard.webservice import ratecontrol


class StreamingOptionsPage(OptionsPage):
    NAME = "meta_streaming"
    TITLE = N_("Streaming Metadata")
    PARENT = "plugins"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        "rate_limit_ms": {"widgets": ["rate_limit_spinbox"]},
        "cover_size": {"widgets": ["cover_size_combo"]},
        "tag_explicit": {"widgets": ["explicit_checkbox"]},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout(self)

        # Rate Limit Group
        rate_group = QtWidgets.QGroupBox(_("Request Rate Limit"), self)
        rate_layout = QtWidgets.QHBoxLayout(rate_group)
        rate_label = QtWidgets.QLabel(_("Minimum delay between requests (ms):"), rate_group)
        self.rate_limit_spinbox = QtWidgets.QSpinBox(rate_group)
        self.rate_limit_spinbox.setRange(50, 2000)
        self.rate_limit_spinbox.setSingleStep(25)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_limit_spinbox)
        rate_layout.addStretch()
        layout.addWidget(rate_group)

        # Cover Art Group
        cover_group = QtWidgets.QGroupBox(_("Cover Art Settings"), self)
        cover_layout = QtWidgets.QHBoxLayout(cover_group)
        cover_label = QtWidgets.QLabel(_("Preferred Cover Art Size:"), cover_group)
        self.cover_size_combo = QtWidgets.QComboBox(cover_group)
        self.cover_size_combo.addItem(_("XL (1000x1000)"), userData="xl")
        self.cover_size_combo.addItem(_("Large (500x500)"), userData="big")
        self.cover_size_combo.addItem(_("Medium (250x250)"), userData="medium")
        self.cover_size_combo.addItem(_("Small (56x56)"), userData="small")
        cover_layout.addWidget(cover_label)
        cover_layout.addWidget(self.cover_size_combo)
        cover_layout.addStretch()
        layout.addWidget(cover_group)

        # Tagging Group
        tag_group = QtWidgets.QGroupBox(_("Tagging Settings"), self)
        tag_layout = QtWidgets.QVBoxLayout(tag_group)
        self.explicit_checkbox = QtWidgets.QCheckBox(_("Tag explicit tracks (~explicit)"), tag_group)
        tag_layout.addWidget(self.explicit_checkbox)
        layout.addWidget(tag_group)

        layout.addStretch()

    def load(self):
        self.rate_limit_spinbox.setValue(self.api.plugin_config["rate_limit_ms"])

        cover_size = self.api.plugin_config["cover_size"]
        index = self.cover_size_combo.findData(cover_size)
        if index >= 0:
            self.cover_size_combo.setCurrentIndex(index)

        self.explicit_checkbox.setChecked(self.api.plugin_config["tag_explicit"])

    def save(self):
        rate_limit = self.rate_limit_spinbox.value()
        self.api.plugin_config["rate_limit_ms"] = rate_limit
        ratecontrol.set_minimum_delay_for_url("https://api.deezer.com", rate_limit)

        self.api.plugin_config["cover_size"] = self.cover_size_combo.currentData()
        self.api.plugin_config["tag_explicit"] = self.explicit_checkbox.isChecked()
