from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox, QFormLayout
)

from symphony.core import radio as radio_api
from symphony.ui import theme as theme_mod


class RadioDialog(QDialog):
    """Browse/search live internet radio stations, or add one by direct
    stream URL. Emits station_chosen(name, url) when the user adds a
    station to Symphony's playlist."""

    station_chosen = pyqtSignal(str, str)  # name, url

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Internet Radio")
        self.resize(460, 420)
        self.setStyleSheet(theme_mod.readable_dialog_qss(
            config.get("ui_font_family", ""), config.get("ui_font_size", 11)))
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        # Favorites comes first: once someone has saved stations, that's
        # almost always what they're reopening this dialog to reach, so it
        # shouldn't be the third tab they have to click through to find.
        self._favorites_tab_index = tabs.addTab(self._build_favorites_tab(), "")
        tabs.addTab(self._build_browse_tab(), "Browse Stations")
        tabs.addTab(self._build_url_tab(), "Add by URL")
        layout.addWidget(tabs)
        self._tabs = tabs
        self._update_favorites_tab_label()

    def show_favorites(self):
        """Open the dialog straight to the Favorites tab — a one-click path
        to a saved station instead of Options -> Internet Radio -> switch
        tabs every time."""
        self._tabs.setCurrentIndex(self._favorites_tab_index)
        self.show()
        self.raise_()
        self.activateWindow()

    def _update_favorites_tab_label(self):
        count = len(self.config.get("radio_favorites", []))
        self._tabs.setTabText(self._favorites_tab_index, f"★ Favorites ({count})")

    # ---------------- Browse (Radio Browser API) ----------------
    def _build_browse_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel("Search live internet radio stations from the free "
                       "Radio-Browser directory.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#8892a6; font-size:10px;")
        v.addWidget(note)

        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("Station name or genre (e.g. jazz, lofi, BBC)…")
        self.query.returnPressed.connect(self._search)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search)
        top_btn = QPushButton("Top Stations")
        top_btn.clicked.connect(self._load_top)
        row.addWidget(self.query, 1)
        row.addWidget(search_btn)
        row.addWidget(top_btn)
        v.addLayout(row)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self._add_selected)
        v.addWidget(self.results, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add to Playlist")
        add_btn.clicked.connect(self._add_selected)
        fav_btn = QPushButton("Add to Favorites")
        fav_btn.clicked.connect(self._favorite_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(fav_btn)
        v.addLayout(btn_row)

        self._data = []
        return w

    def _search(self):
        query = self.query.text().strip()
        self._run_search(query=query)

    def _load_top(self):
        self.query.clear()
        self._run_search(query="")

    def _run_search(self, query):
        self.results.clear()
        try:
            self._data = (radio_api.search(query=query, limit=40) if query
                          else radio_api.top_stations(limit=40))
        except Exception as e:
            QMessageBox.warning(self, "Station search failed", str(e))
            return
        for s in self._data:
            bitrate = f"{s.bitrate}kbps " if s.bitrate else ""
            label = f"{s.name} — {bitrate}{s.codec} [{s.country or 'Unknown'}]"
            self.results.addItem(label)

    def _add_selected(self):
        row = self.results.currentRow()
        if row < 0 or row >= len(self._data):
            return
        station = self._data[row]
        self.station_chosen.emit(station.name, station.url)

    def _favorite_selected(self):
        row = self.results.currentRow()
        if row < 0 or row >= len(self._data):
            return
        station = self._data[row]
        favs = list(self.config.get("radio_favorites", []))
        if not any(f["url"] == station.url for f in favs):
            favs.append({"name": station.name, "url": station.url})
            self.config["radio_favorites"] = favs
        self._refresh_favorites()

    # ---------------- Add by URL ----------------
    def _build_url_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        form = QFormLayout()
        self.url_name = QLineEdit()
        self.url_name.setPlaceholderText("Station name")
        self.url_stream = QLineEdit()
        self.url_stream.setPlaceholderText("https://stream.example.com/live.mp3")
        form.addRow("Name:", self.url_name)
        form.addRow("Stream URL:", self.url_stream)
        v.addLayout(form)

        add_row = QHBoxLayout()
        add_btn = QPushButton("Add to Playlist")
        add_btn.clicked.connect(self._add_url)
        fav_btn = QPushButton("Add to Favorites")
        fav_btn.clicked.connect(self._favorite_url)
        add_row.addWidget(add_btn)
        add_row.addWidget(fav_btn)
        v.addLayout(add_row)
        v.addStretch()
        return w

    def _add_url(self):
        name, url = self._url_fields()
        if not url:
            return
        self.station_chosen.emit(name, url)

    def _favorite_url(self):
        name, url = self._url_fields()
        if not url:
            return
        favs = list(self.config.get("radio_favorites", []))
        if not any(f["url"] == url for f in favs):
            favs.append({"name": name, "url": url})
            self.config["radio_favorites"] = favs
        self._refresh_favorites()

    def _url_fields(self):
        name = self.url_name.text().strip() or "Internet Radio"
        url = self.url_stream.text().strip()
        if url and not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Invalid URL", "Stream URL must start with http:// or https://")
            return name, ""
        return name, url

    # ---------------- Favorites ----------------
    def _build_favorites_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        note = QLabel("Your saved stations. Double-click one to add it to "
                       "the playlist, or use Options → ★ Radio Favorites "
                       "from the main window to jump straight here.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#8892a6; font-size:10px;")
        v.addWidget(note)
        self.fav_list = QListWidget()
        self.fav_list.itemDoubleClicked.connect(self._add_favorite_selected)
        v.addWidget(self.fav_list, 1)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add to Playlist")
        add_btn.clicked.connect(self._add_favorite_selected)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_favorite)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        v.addLayout(btn_row)
        self._refresh_favorites()
        return w

    def _refresh_favorites(self):
        self.fav_list.clear()
        for fav in self.config.get("radio_favorites", []):
            item = QListWidgetItem(f"★ {fav['name']}")
            item.setData(1000, fav["url"])
            item.setData(1001, fav["name"])  # clean name, without the star
            self.fav_list.addItem(item)
        # Guard: during initial dialog construction this tab is built
        # before self._tabs exists; _build_ui updates the label once
        # everything is wired up.
        if hasattr(self, "_tabs"):
            self._update_favorites_tab_label()

    def _add_favorite_selected(self):
        item = self.fav_list.currentItem()
        if not item:
            return
        self.station_chosen.emit(item.data(1001), item.data(1000))

    def _remove_favorite(self):
        row = self.fav_list.currentRow()
        favs = list(self.config.get("radio_favorites", []))
        if 0 <= row < len(favs):
            del favs[row]
            self.config["radio_favorites"] = favs
            self._refresh_favorites()
