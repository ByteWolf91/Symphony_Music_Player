from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QLabel, QListWidget,
                             QListWidgetItem, QPushButton, QMenu, QAbstractItemView)

from symphony.ui.track_table import (TrackWindow, make_table, fill_table, track_matches,
                                     row_track, MENU_QSS)


class PlaylistWindow(TrackWindow):
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
    # visibility_changed (inherited) keeps the main window's toggle button in
    # sync, including when the window is closed from its own titlebar.

    def __init__(self, parent=None, font_family="", font_size=11,
                 list_font_family="", list_font_size=0):
        super().__init__("Symphony Playlist", parent, font_family, font_size,
                         list_font_family, list_font_size)
        self.setMinimumSize(640, 320)
        self.resize(760, 460)
        # Maps a row in the radio-stations panel back to its index in the
        # full playlist, so double-clicking there plays the right track.
        self._radio_index_map = []
        self._table_index_map = []
        self._tracks = []
        self._build_ui()
        self._register_views(self.table, self.radio_list)
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._build_titlebar(root, "PLAYLIST EDITOR")
        self._build_search(root, "Search playlist by artist, album or song…")

        # Rows always equal playlist indices here (no sorting), so a row
        # number can be handed straight back to the main window.
        self.table = make_table(["#", "Artist", "Song", "Album", "Duration"])
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellDoubleClicked.connect(
            lambda row, _c: self._play_table_row(row))
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.keyPressEvent = self._table_key_press  # Enter plays the row
        root.addWidget(self.table, 1)

        # A dedicated radio-stations section, separate from the main list, so
        # saved/queued stations are easy to spot. Only takes up space once
        # there is at least one radio track in the playlist.
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

    # ---------------- content ----------------
    def refresh(self, tracks, current_index: int, total_seconds: float):
        scroll = self.table.verticalScrollBar().value()
        selected = self.table.currentRow()
        self._tracks = list(tracks)
        table_tracks = [
            (index, track) for index, track in enumerate(self._tracks)
            if track.source != "radio"
        ]
        self._table_index_map = [index for index, _track in table_tracks]
        fill_table(
            self.table,
            [track for _index, track in table_tracks],
            current_index,
            numbered=True,
            track_indices=self._table_index_map,
        )

        self.radio_list.clear()
        self._radio_index_map = []
        for i, track in enumerate(self._tracks):
            if track.source == "radio":
                marker = "▶ " if i == current_index else ""
                name = (track.title or "").strip() or (track.uri or "Unnamed station")
                item = QListWidgetItem(f"{marker}{name}")
                item.setToolTip(track.uri or "")
                self.radio_list.addItem(item)
                self._radio_index_map.append(i)
        self.radio_header_label.setText(f"📻 RADIO STATIONS ({len(self._radio_index_map)})")
        self.radio_section.setVisible(bool(self._radio_index_map))

        m, s = divmod(int(total_seconds), 60)
        self.total_label.setText(f"{m:02d}:{s:02d}")

        if 0 <= selected < self.table.rowCount():
            self.table.setCurrentCell(selected, 1)
        self.table.verticalScrollBar().setValue(scroll)
        # Re-apply any active search, since the rows were just rebuilt.
        self._apply_filter()

    def _filter_done(self, matched, total, active):
        self.count_label.setText(f"{matched} of {total} items" if active else f"{total} items")
        query = self.search_box.text().strip().lower()
        for row in range(self.radio_list.count()):
            idx = self._radio_index_map[row] if row < len(self._radio_index_map) else -1
            track = self._tracks[idx] if 0 <= idx < len(self._tracks) else None
            self.radio_list.item(row).setHidden(
                bool(query) and track is not None and not track_matches(track, query))

    def selected_index(self) -> int:
        row = self.table.currentRow()
        return self._playlist_index_for_row(row)

    # ---------------- interaction ----------------
    def _playlist_index_for_row(self, row):
        if row < 0 or row >= self.table.rowCount():
            return -1
        track = row_track(self.table, row)
        if track is not None:
            for index, candidate in enumerate(self._tracks):
                if candidate is track:
                    return index
        return (
            self._table_index_map[row]
            if row < len(self._table_index_map)
            else -1
        )

    def _play_table_row(self, row):
        index = self._playlist_index_for_row(row)
        if index >= 0:
            self.play_index_requested.emit(index)

    def _on_radio_item_double_clicked(self, item):
        row = self.radio_list.row(item)
        if 0 <= row < len(self._radio_index_map):
            self.play_index_requested.emit(self._radio_index_map[row])

    def _table_key_press(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = self.table.currentRow()
            self._play_table_row(row)
            return
        type(self.table).keyPressEvent(self.table, event)

    def _on_remove_clicked(self):
        self.remove_index_requested.emit(self.selected_index())

    def _show_context_menu(self, pos):
        # Act on the row under the cursor (not whatever was selected before).
        row = self.table.rowAt(pos.y())
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)
        if row >= 0:
            self.table.selectRow(row)
            index = self._playlist_index_for_row(row)
            menu.addAction("Play", lambda: self.play_index_requested.emit(index))
            menu.addAction("Remove Track", lambda: self.remove_index_requested.emit(index))
            menu.addSeparator()
        menu.addAction("Add File(s)…", self.add_files_requested.emit)
        menu.addAction("Add Folder…", self.add_folder_requested.emit)
        menu.addSeparator()
        menu.addAction("Clear Playlist", self.clear_requested.emit)
        menu.exec_(self.table.viewport().mapToGlobal(pos))
