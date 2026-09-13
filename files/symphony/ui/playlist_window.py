from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QListWidget, QPushButton)


class PlaylistWindow(QWidget):
    play_index_requested = pyqtSignal(int)
    remove_index_requested = pyqtSignal(int)
    clear_requested = pyqtSignal()
    sort_requested = pyqtSignal()
    dedupe_requested = pyqtSignal()
    add_files_requested = pyqtSignal()
    add_folder_requested = pyqtSignal()
    add_cd_requested = pyqtSignal()
    youtube_download_requested = pyqtSignal()
    radio_favorites_requested = pyqtSignal()
    save_playlist_requested = pyqtSignal()
    load_playlist_requested = pyqtSignal()
    # Emitted whenever the window is actually shown/hidden (including via its
    # own titlebar close button), so the main window's toggle button stays
    # in sync instead of needing a second click to react.
    visibility_changed = pyqtSignal(bool)

    SOURCE_ICONS = {"radio": "📻 ", "cd": "💿 "}

    def __init__(self, parent=None, font_family="", font_size=11):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Symphony Playlist")
        self.setMinimumSize(520, 300)
        self.resize(620, 430)
        self._font_family = font_family
        self._font_size = font_size
        # Maps a row in the radio-stations panel back to its index in the
        # full playlist, so double-clicking there plays the right track.
        self._radio_index_map = []
        self._apply_font_style()
        self._drag_pos = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titlebar = QWidget()
        titlebar.setFixedHeight(16)
        titlebar.setStyleSheet("background:#152048;")
        tb_layout = QHBoxLayout(titlebar)
        tb_layout.setContentsMargins(4, 0, 4, 0)
        label = QLabel("PLAYLIST EDITOR")
        label.setStyleSheet("color:#cfe0ff; font-weight:bold;")
        close_btn = QPushButton("×")
        close_btn.setFixedSize(14, 14)
        close_btn.clicked.connect(self.hide)
        tb_layout.addWidget(label)
        tb_layout.addStretch()
        tb_layout.addWidget(close_btn)
        titlebar.mousePressEvent = self._start_drag
        titlebar.mouseMoveEvent = self._do_drag
        root.addWidget(titlebar)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "background:#10141c; color:#f4f7fb; border:1px solid #465166;")
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        # Enter plays the selected row; Up/Down/PageUp/PageDown navigation
        # is QListWidget's native behavior already.
        self.list_widget.keyPressEvent = self._list_key_press
        root.addWidget(self.list_widget, 1)

        # A dedicated radio-stations section, separate from the main list,
        # so saved/queued stations are easy to spot and jump to instead of
        # being buried among local files. Only takes up space once there's
        # at least one radio track in the playlist.
        self.radio_section = QWidget()
        radio_layout = QVBoxLayout(self.radio_section)
        radio_layout.setContentsMargins(0, 4, 0, 0)
        radio_layout.setSpacing(2)
        self.radio_header_label = QLabel("📻 RADIO STATIONS (0)")
        self.radio_header_label.setStyleSheet(
            "color:#8fc7ff; font-weight:bold; font-size:10px; padding:2px 2px;")
        radio_layout.addWidget(self.radio_header_label)
        self.radio_list = QListWidget()
        self.radio_list.setMaximumHeight(84)
        self.radio_list.setStyleSheet(
            "background:#10141c; color:#f4f7fb; border:1px solid #465166;")
        self.radio_list.itemDoubleClicked.connect(self._on_radio_item_double_clicked)
        radio_layout.addWidget(self.radio_list)
        root.addWidget(self.radio_section)
        self.radio_section.setVisible(False)

        footer = QHBoxLayout()
        self.count_label = QLabel("0 items")
        self.total_label = QLabel("00:00")
        for lab in (self.count_label, self.total_label):
            lab.setStyleSheet("color:#9ab;")
        footer.addWidget(self.count_label)
        footer.addStretch()
        footer.addWidget(self.total_label)
        root.addLayout(footer)

        # Row 1: ways to add content to the playlist.
        add_row = QHBoxLayout()
        add_btn = QPushButton("ADD FILES")
        add_folder_btn = QPushButton("ADD FOLDER")
        add_cd_btn = QPushButton("SELECT CD DRIVE…")
        add_cd_btn.setToolTip("Choose an optical drive and add its tracks")
        youtube_btn = QPushButton("YOUTUBE AUDIO…")
        youtube_btn.setToolTip("Download audio from a YouTube video or playlist")
        fav_btn = QPushButton("★ RADIO STATIONS")
        fav_btn.setToolTip("Open your saved radio stations")
        add_btn.clicked.connect(self.add_files_requested.emit)
        add_folder_btn.clicked.connect(self.add_folder_requested.emit)
        add_cd_btn.clicked.connect(self.add_cd_requested.emit)
        youtube_btn.clicked.connect(self.youtube_download_requested.emit)
        fav_btn.clicked.connect(self.radio_favorites_requested.emit)
        for b in (add_btn, add_folder_btn, add_cd_btn, youtube_btn, fav_btn):
            add_row.addWidget(b)
        root.addLayout(add_row)

        # Row 2: managing what's already in the list.
        manage_row = QHBoxLayout()
        remove_btn = QPushButton("REMOVE")
        clear_btn = QPushButton("CLEAR")
        sort_btn = QPushButton("SORT")
        dedupe_btn = QPushButton("REMOVE DUPLICATES")
        remove_btn.clicked.connect(self._on_remove_clicked)
        clear_btn.clicked.connect(self.clear_requested.emit)
        sort_btn.clicked.connect(self.sort_requested.emit)
        dedupe_btn.clicked.connect(self.dedupe_requested.emit)
        for b in (remove_btn, clear_btn, sort_btn, dedupe_btn):
            manage_row.addWidget(b)
        root.addLayout(manage_row)

        # Row 3: playlist file operations.
        pl_row = QHBoxLayout()
        save_btn = QPushButton("SAVE PLAYLIST…")
        load_btn = QPushButton("LOAD PLAYLIST…")
        save_btn.clicked.connect(self.save_playlist_requested.emit)
        load_btn.clicked.connect(self.load_playlist_requested.emit)
        for b in (save_btn, load_btn):
            pl_row.addWidget(b)
        root.addLayout(pl_row)

    def set_font(self, font_family="", font_size=11):
        self._font_family = font_family
        self._font_size = font_size
        self._apply_font_style()

    def set_skin(self, skin):
        """Apply classic pledit.txt colors when a Winamp skin provides them."""
        colors = getattr(skin, "pledit_colors", {}) if skin else {}

        def color(name, fallback):
            raw = colors.get(name.lower(), "").replace(" ", "")
            if raw.startswith("#"):
                return raw
            parts = raw.split(",")
            if len(parts) >= 3 and all(part.lstrip("-").isdigit() for part in parts[:3]):
                try:
                    r, g, b = (max(0, min(255, int(part))) for part in parts[:3])
                    return f"rgb({r},{g},{b})"
                except ValueError:
                    pass
            return fallback

        bg = color("normalbg", "#10141c")
        text = color("normal", "#f4f7fb")
        selected_bg = color("selectionbg", "#214d3a")
        selected = color("selection", "#ffffff")
        list_qss = (
            f"QListWidget {{ background:{bg}; color:{text}; "
            f"border:1px solid #465166; }}"
            f"QListWidget::item:selected {{ background:{selected_bg}; "
            f"color:{selected}; }}"
        )
        self.list_widget.setStyleSheet(list_qss)
        self.radio_list.setStyleSheet(list_qss)

    def _apply_font_style(self):
        family = self._font_family.strip() or "Segoe UI, Noto Sans, sans-serif"
        size = max(8, min(24, int(self._font_size or 11)))
        self.setStyleSheet(
            f"QWidget {{ background:#171b24; border:1px solid #15171d; "
            f"font-family:{family}; font-size:{size}px; }}"
            f"QListWidget {{ background:#10141c; color:#f4f7fb; "
            f"font-family:{family}; font-size:{size}px; border:1px solid #465166; }}"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def refresh(self, tracks, current_index: int, total_seconds: float):
        self.list_widget.clear()
        self.radio_list.clear()
        self._radio_index_map = []
        for i, track in enumerate(tracks):
            marker = "▶ " if i == current_index else f"{i + 1}. "
            icon = self.SOURCE_ICONS.get(track.source, "")
            display = f"{track.artist} - {track.title}" if track.artist else track.title
            self.list_widget.addItem(f"{marker}{icon}{display}")
            if track.source == "radio":
                radio_marker = "▶ " if i == current_index else ""
                self.radio_list.addItem(f"{radio_marker}{track.title}")
                self._radio_index_map.append(i)
        self.radio_header_label.setText(f"📻 RADIO STATIONS ({len(self._radio_index_map)})")
        self.radio_section.setVisible(bool(self._radio_index_map))
        self.count_label.setText(f"{len(tracks)} items")
        m, s = divmod(int(total_seconds), 60)
        self.total_label.setText(f"{m:02d}:{s:02d}")

    def selected_index(self) -> int:
        return self.list_widget.currentRow()

    def _on_item_double_clicked(self, item):
        self.play_index_requested.emit(self.list_widget.row(item))

    def _on_radio_item_double_clicked(self, item):
        row = self.radio_list.row(item)
        if 0 <= row < len(self._radio_index_map):
            self.play_index_requested.emit(self._radio_index_map[row])

    def _list_key_press(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = self.list_widget.currentRow()
            if row >= 0:
                self.play_index_requested.emit(row)
            return
        QListWidget.keyPressEvent(self.list_widget, event)

    def _on_remove_clicked(self):
        self.remove_index_requested.emit(self.list_widget.currentRow())

    def _start_drag(self, event):
        self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _do_drag(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
