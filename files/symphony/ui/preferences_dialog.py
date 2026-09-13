from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QCheckBox,
    QSpinBox, QComboBox, QDialogButtonBox, QFontComboBox
)

from symphony.ui import theme as theme_mod


class PreferencesDialog(QDialog):
    """Full Symphony preferences, organized into tabs."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Symphony Preferences")
        self.setMinimumWidth(420)
        self.setStyleSheet(theme_mod.readable_dialog_qss(
            config.get("ui_font_family", ""), config.get("ui_font_size", 11)))

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_playback_tab(), "Playback")
        tabs.addTab(self._build_interface_tab(), "Interface")
        root.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # ---------------- General ----------------
    def _build_general_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.autoplay_import = QCheckBox("Start playing when files are imported")
        self.autoplay_import.setChecked(self.config.get("autoplay_import", True))

        self.scan_subfolders = QCheckBox("Scan subfolders when importing a folder")
        self.scan_subfolders.setChecked(self.config.get("scan_subfolders", True))

        self.confirm_clear = QCheckBox("Ask before clearing the playlist")
        self.confirm_clear.setChecked(self.config.get("confirm_clear", True))

        self.confirm_quit = QCheckBox("Ask before quitting Symphony")
        self.confirm_quit.setChecked(self.config.get("confirm_quit", False))

        form.addRow(self.autoplay_import)
        form.addRow(self.scan_subfolders)
        form.addRow(self.confirm_clear)
        form.addRow(self.confirm_quit)
        return w

    # ---------------- Playback ----------------
    def _build_playback_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.remember_volume = QCheckBox("Remember volume between sessions")
        self.remember_volume.setChecked(self.config.get("remember_volume", True))

        self.read_tags = QCheckBox("Read artist / genre / title tags on import")
        self.read_tags.setChecked(self.config.get("read_tags", True))

        form.addRow(self.remember_volume)
        form.addRow(self.read_tags)
        return w

    # ---------------- Interface ----------------
    def _build_interface_tab(self):
        w = QWidget()
        form = QFormLayout(w)

        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.theme.setCurrentIndex(1 if self.config.get("theme", "dark") == "light" else 0)

        self.restore_skin = QCheckBox("Restore the last skin on startup")
        self.restore_skin.setChecked(self.config.get("restore_skin", True))

        self.always_on_top = QCheckBox("Keep Symphony above other windows")
        self.always_on_top.setChecked(self.config.get("always_on_top", False))

        self.show_artist_genre = QCheckBox("Show artist / genre in the now-playing display")
        self.show_artist_genre.setChecked(self.config.get("show_artist_genre", True))

        self.ui_scale = QSpinBox()
        self.ui_scale.setRange(75, 200)
        self.ui_scale.setSingleStep(5)
        self.ui_scale.setSuffix("%")
        self.ui_scale.setValue(int(self.config.get("ui_scale", 100)))
        self.ui_scale.setToolTip("Applied when the window is next opened.")

        self.font_family = QFontComboBox()
        saved_family = self.config.get("ui_font_family", "")
        if saved_family:
            self.font_family.setCurrentText(saved_family)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setSuffix(" pt")
        self.font_size.setValue(int(self.config.get("ui_font_size", 11)))

        form.addRow("Theme:", self.theme)
        form.addRow(self.restore_skin)
        form.addRow(self.always_on_top)
        form.addRow(self.show_artist_genre)
        form.addRow("UI scale (next launch):", self.ui_scale)
        form.addRow("Font:", self.font_family)
        form.addRow("Font size:", self.font_size)
        return w

    def save(self):
        self.config.update({
            "autoplay_import": self.autoplay_import.isChecked(),
            "scan_subfolders": self.scan_subfolders.isChecked(),
            "confirm_clear": self.confirm_clear.isChecked(),
            "confirm_quit": self.confirm_quit.isChecked(),
            "remember_volume": self.remember_volume.isChecked(),
            "read_tags": self.read_tags.isChecked(),
            "theme": "light" if self.theme.currentIndex() == 1 else "dark",
            "restore_skin": self.restore_skin.isChecked(),
            "always_on_top": self.always_on_top.isChecked(),
            "show_artist_genre": self.show_artist_genre.isChecked(),
            "ui_scale": self.ui_scale.value(),
            "ui_font_family": self.font_family.currentFont().family(),
            "ui_font_size": self.font_size.value(),
        })
