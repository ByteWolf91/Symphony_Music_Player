from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QFormLayout, QCheckBox,
    QSpinBox, QComboBox, QDialogButtonBox, QFontComboBox, QPushButton,
    QMessageBox, QFileDialog, QLabel
)

from symphony import fonts as fonts_mod
from symphony.ui import theme as theme_mod


class FontRow(QWidget):
    """One font choice: a 'use default' checkbox, a family picker (each name
    drawn in its own face) and a pixel size."""

    def __init__(self, family, size, default_label, size_follows_default=False,
                 size_range=(8, 32), parent=None):
        super().__init__(parent)
        self._size_follows_default = size_follows_default
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.use_default = QCheckBox(default_label)
        self.combo = QFontComboBox()
        self.spin = QSpinBox()
        self.spin.setRange(*size_range)
        self.spin.setSuffix(" px")
        if family:
            self.combo.setCurrentFont(QFont(family))
        self.spin.setValue(int(size) if size else max(size_range[0], 11))
        self.use_default.setChecked(not family)
        self.use_default.toggled.connect(self._sync)
        lay.addWidget(self.use_default)
        lay.addWidget(self.combo, 1)
        lay.addWidget(self.spin)
        self._sync()
        self._size_default = not size

    def _sync(self):
        default = self.use_default.isChecked()
        self.combo.setEnabled(not default)
        if self._size_follows_default:
            self.spin.setEnabled(not default)

    def family(self):
        return "" if self.use_default.isChecked() else self.combo.currentFont().family()

    def size(self):
        if self._size_follows_default and self.use_default.isChecked():
            return 0
        return self.spin.value()

    def refresh_fonts(self):
        """Re-read the font database (after a font file was added)."""
        keep = self.combo.currentFont()
        self.combo.setWritingSystem(self.combo.writingSystem())
        self.combo.setCurrentFont(keep)


class PreferencesDialog(QDialog):
    """Full Symphony preferences, organized into tabs."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Symphony Preferences")
        self.setMinimumWidth(560)
        self._new_font_files = []
        self.setStyleSheet(theme_mod.readable_dialog_qss(
            config.get("ui_font_family", ""), config.get("ui_font_size", 11)))

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_playback_tab(), "Playback")
        tabs.addTab(self._build_interface_tab(), "Interface")
        tabs.addTab(self._build_fonts_tab(), "Fonts")
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

        self.restore_playlist = QCheckBox("Restore the last playlist on startup")
        self.restore_playlist.setChecked(self.config.get("restore_playlist", True))

        self.remember_playlists = QCheckBox("Remember previously saved playlists")
        self.remember_playlists.setChecked(self.config.get("remember_playlists", True))
        self.remember_playlists.setToolTip(
            "Keeps a Recent Playlists list under Options for quick reopening.")

        form.addRow(self.restore_playlist)
        form.addRow(self.remember_playlists)
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

        self.read_tags = QCheckBox("Read artist / album / genre / title tags on import")
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

        self.show_artist_genre = QCheckBox("Show artist / album / genre in the now-playing display")
        self.show_artist_genre.setChecked(self.config.get("show_artist_genre", True))

        self.ui_scale = QSpinBox()
        self.ui_scale.setRange(75, 200)
        self.ui_scale.setSingleStep(5)
        self.ui_scale.setSuffix("%")
        self.ui_scale.setValue(int(self.config.get("ui_scale", 100)))
        self.ui_scale.setToolTip("Applied when the window is next opened.")

        form.addRow("Theme:", self.theme)
        form.addRow(self.restore_skin)
        form.addRow(self.always_on_top)
        form.addRow(self.show_artist_genre)
        form.addRow("UI scale (next launch):", self.ui_scale)
        return w

    # ---------------- Fonts ----------------
    def _build_fonts_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        note = QLabel("Pick any installed font, or add your own .ttf / .otf file. "
                      "Changes apply as soon as you press OK.")
        note.setWordWrap(True)

        self.font_ui = FontRow(self.config.get("ui_font_family", ""),
                               self.config.get("ui_font_size", 11),
                               "System default", size_range=(8, 24))
        self.font_list = FontRow(self.config.get("list_font_family", ""),
                                 self.config.get("list_font_size", 0),
                                 "Same as interface", size_follows_default=True,
                                 size_range=(8, 32))
        self.font_display = FontRow(self.config.get("display_font_family", ""),
                                    self.config.get("display_font_size", 11),
                                    "Courier New", size_range=(8, 20))
        add_font = QPushButton("Add font file…")
        add_font.clicked.connect(self._add_font_file)

        form.addRow(note)
        form.addRow("Interface:", self.font_ui)
        form.addRow("Playlist:", self.font_list)
        form.addRow("Now-playing display:", self.font_display)
        form.addRow(add_font)
        return w

    def _add_font_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Add font file", "", fonts_mod.FONT_FILE_FILTER)
        if not path:
            return
        families = fonts_mod.register_font_file(path)
        if not families:
            QMessageBox.warning(self, "Font not added", "That file couldn't be loaded as a font.")
            return
        self._new_font_files.append(path)
        for row in (self.font_ui, self.font_list, self.font_display):
            row.refresh_fonts()
        QMessageBox.information(
            self, "Font added",
            "Added: " + ", ".join(families) + "\nUncheck the default box on a row and pick it from the list.")

    def save(self):
        self.config.update({
            "remember_playlists": self.remember_playlists.isChecked(),
            "restore_playlist": self.restore_playlist.isChecked(),
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
            "ui_font_family": self.font_ui.family(),
            "ui_font_size": self.font_ui.size(),
            "list_font_family": self.font_list.family(),
            "list_font_size": self.font_list.size(),
            "display_font_family": self.font_display.family(),
            "display_font_size": self.font_display.size(),
        })
        files = list(self.config.get("custom_font_files", []))
        for path in self._new_font_files:
            if path not in files:
                files.append(path)
        self.config["custom_font_files"] = files
