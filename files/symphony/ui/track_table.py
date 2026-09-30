"""Shared pieces for track-table windows (currently just the Playlist).

Provides a tidy table (artist / song / album / duration), a shared search-box
behaviour, and consistent fonts/skin colours — kept separate from
playlist_window.py so another track-table window can reuse it later.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView)

from symphony.ui import theme as theme_mod

SOURCE_ICONS = {"radio": "📻 ", "cd": "💿 "}
DEFAULT_COLORS = {
    "bg": "#10141c", "text": "#f4f7fb",
    "selected_bg": "#214d3a", "selected": "#ffffff",
}
PLAYING_COLOR = "#7fff9f"

# Context menus are children of dark windows, so give them explicit colours
# instead of relying on whichever app theme is active.
MENU_QSS = """
QMenu { background:#1c2230; color:#f4f7fb; border:1px solid #465166; padding:4px; }
QMenu::item { padding:6px 22px 6px 12px; border-radius:3px; background:transparent; color:#f4f7fb; }
QMenu::item:selected { background:#2f5fd0; color:#ffffff; }
QMenu::item:disabled { color:#7b869c; }
QMenu::separator { height:1px; background:#465166; margin:4px 6px; }
"""


def fmt_duration(seconds) -> str:
    if not seconds or seconds <= 0:
        return "—"
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def track_matches(track, query: str) -> bool:
    """True if every word in the query appears in the artist, song title,
    album or genre (case-insensitive). Empty query matches everything."""
    words = (query or "").lower().split()
    if not words:
        return True
    haystack = " ".join((track.artist or "", track.title or "",
                         track.album or "", track.genre or "")).lower()
    return all(w in haystack for w in words)


class SortItem(QTableWidgetItem):
    """Table cell that sorts by a hidden key (numbers sort as numbers,
    text case-insensitively) instead of by its display string."""

    def __lt__(self, other):
        a = self.data(Qt.UserRole + 1)
        b = other.data(Qt.UserRole + 1)
        if a is not None and b is not None:
            try:
                return a < b
            except TypeError:
                pass
        return super().__lt__(other)


def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(22)
    table.setShowGrid(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.ElideRight)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setContextMenuPolicy(Qt.CustomContextMenu)
    header = table.horizontalHeader()
    header.setHighlightSections(False)
    header.setStretchLastSection(False)
    for col, name in enumerate(headers):
        if name == "#":
            header.setSectionResizeMode(col, QHeaderView.Fixed)
            table.setColumnWidth(col, 46)
        elif name == "Duration":
            header.setSectionResizeMode(col, QHeaderView.Fixed)
            table.setColumnWidth(col, 76)
        elif name == "Song":
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        else:  # Artist / Album
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            table.setColumnWidth(col, 160)
    return table


def fill_table(table, tracks, current_index=-1, numbered=True, track_indices=None):
    """Rebuild the table rows. Column 0 of every row carries the Track
    object in Qt.UserRole so callers can map a row back to its track even
    after the user sorts."""
    table.setSortingEnabled(False)
    table.setUpdatesEnabled(False)
    table.clearContents()
    table.setRowCount(len(tracks))
    playing = QBrush(QColor(PLAYING_COLOR))
    bold = table.font()
    bold.setBold(True)
    for row, t in enumerate(tracks):
        track_index = (
            track_indices[row]
            if track_indices is not None and row < len(track_indices)
            else row
        )
        is_current = track_index == current_index
        if t.source == "radio":
            dur_text, dur_key = "LIVE", 0
        else:
            dur_text, dur_key = fmt_duration(t.duration), t.duration or 0
        cells = []
        if numbered:
            cells.append(("▶" if is_current else str(track_index + 1), track_index))
        cells += [
            (t.artist or "—", (t.artist or "").lower()),
            (SOURCE_ICONS.get(t.source, "") + (t.title or ""), (t.title or "").lower()),
            (t.album or "—", (t.album or "").lower()),
            (dur_text, dur_key),
        ]
        last = len(cells) - 1
        for col, (text, key) in enumerate(cells):
            item = SortItem(text)
            item.setData(Qt.UserRole + 1, key)
            if col == 0:
                item.setData(Qt.UserRole, t)
            if numbered and col == 0:
                item.setTextAlignment(Qt.AlignCenter)
            elif col == last:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if is_current:
                item.setForeground(playing)
                item.setFont(bold)
            table.setItem(row, col, item)
    table.setUpdatesEnabled(True)


def row_track(table, row):
    item = table.item(row, 0)
    return item.data(Qt.UserRole) if item is not None else None


def table_qss(colors, family="", size=11) -> str:
    fam = theme_mod.css_family(family)
    size = max(8, min(32, int(size or 11)))
    return f"""
QTableWidget, QListWidget {{
    background:{colors['bg']}; color:{colors['text']};
    border:1px solid #465166; outline:none;
    font-family:{fam}; font-size:{size}px;
}}
QTableWidget::item, QListWidget::item {{
    padding:0 6px; border:none; color:#dfe5f5;
}}
QTableWidget::item:selected, QListWidget::item:selected {{
    background:{colors['selected_bg']}; color:{colors['selected']};
}}
QHeaderView::section {{
    background:#1c2230; color:#cfe0ff; border:none;
    border-bottom:1px solid #465166; border-right:1px solid #2a3244;
    padding:4px 6px; font-weight:bold; font-family:{fam}; font-size:{size}px;
}}
"""


class TrackWindow(QWidget):
    """Frameless, draggable tool window with a title bar, a search box and a
    track table. Subclasses add their own buttons underneath."""

    visibility_changed = pyqtSignal(bool)

    def __init__(self, window_title, parent=None, font_family="", font_size=11,
                 list_font_family="", list_font_size=0):
        super().__init__(parent, Qt.Window)
        self._title_text = window_title
        self.setWindowTitle(window_title)
        self._font_family = font_family
        self._font_size = font_size
        self._list_family = list_font_family
        self._list_size = list_font_size
        self._theme = "dark"
        self._colors = dict(DEFAULT_COLORS)
        self._drag_pos = None
        self._styled_views = []

    # ---- building blocks -------------------------------------------------
    def _build_titlebar(self, root, text):
        titlebar = QWidget()
        titlebar.setFixedHeight(16)
        titlebar.setStyleSheet("background:#152048;")
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(4, 0, 4, 0)
        label = QLabel(text)
        label.setStyleSheet("color:#cfe0ff; font-weight:bold;")
        close = QPushButton("×")
        close.setFixedSize(14, 14)
        close.clicked.connect(self.hide)
        tb.addWidget(label)
        tb.addStretch()
        tb.addWidget(close)
        titlebar.mousePressEvent = self._start_drag
        titlebar.mouseMoveEvent = self._do_drag
        titlebar.mouseReleaseEvent = self._end_drag
        root.addWidget(titlebar)

    def _build_search(self, root, placeholder):
        row = QHBoxLayout()
        row.setContentsMargins(6, 6, 6, 4)
        row.setSpacing(6)
        row.addWidget(QLabel("🔍"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(placeholder)
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self._apply_filter)
        row.addWidget(self.search_box, 1)
        root.addLayout(row)

    def _register_views(self, *views):
        self._styled_views = list(views)

    # ---- search ----------------------------------------------------------
    def _apply_filter(self, text=None):
        query = (self.search_box.text() if text is None else text).strip().lower()
        total = self.table.rowCount()
        matched = 0
        for row in range(total):
            t = row_track(self.table, row)
            hide = bool(query) and t is not None and not track_matches(t, query)
            self.table.setRowHidden(row, hide)
            if not hide:
                matched += 1
        self._filter_done(matched, total, bool(query))

    def _filter_done(self, matched, total, active):
        """Hook for subclasses to update their counters."""

    # ---- fonts / skin ----------------------------------------------------
    def set_font(self, font_family="", font_size=11, list_font_family="", list_font_size=0):
        self._font_family = font_family
        self._font_size = font_size
        self._list_family = list_font_family
        self._list_size = list_font_size
        self._apply_styles()

    def set_theme(self, theme_name="dark"):
        self._theme = theme_name
        self._apply_styles()

    def set_skin(self, skin):
        """Apply classic pledit.txt colors when a Winamp skin provides them."""
        colors = getattr(skin, "pledit_colors", {}) if skin else {}

        def color(name, fallback):
            raw = colors.get(name.lower(), "").replace(" ", "")
            if raw.startswith("#"):
                return raw
            parts = raw.split(",")
            if len(parts) >= 3 and all(p.lstrip("-").isdigit() for p in parts[:3]):
                r, g, b = (max(0, min(255, int(p))) for p in parts[:3])
                return f"rgb({r},{g},{b})"
            return fallback

        self._colors = {
            "bg": color("normalbg", DEFAULT_COLORS["bg"]),
            "text": color("normal", DEFAULT_COLORS["text"]),
            "selected_bg": color("selectionbg", DEFAULT_COLORS["selected_bg"]),
            "selected": color("selection", DEFAULT_COLORS["selected"]),
        }
        self._apply_styles()

    def _apply_styles(self):
        fam = theme_mod.css_family(self._font_family)
        size = max(8, min(32, int(self._font_size or 11)))
        self.setStyleSheet(
            f"QWidget {{ background:#171b24; border:1px solid #15171d; "
            f"font-family:{fam}; font-size:{size}px; }}"
            "QLabel { border:none; background:transparent; color:#dfe5f5; }"
            "QLineEdit { background:#10141c; color:#f4f7fb; border:1px solid #465166; "
            "border-radius:3px; padding:3px 6px; }"
            + self._button_qss()
        )
        qss = table_qss(self._colors, self._list_family or self._font_family,
                        self._list_size or self._font_size)
        for view in self._styled_views:
            view.setStyleSheet(qss)

    def _button_qss(self):
        p = theme_mod.palette(self._theme)
        return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                         stop:0 {p['btn_gradient_top']},
                         stop:1 {p['btn_gradient_bottom']});
            color: {p['text']};
            border: 1px solid {p['btn_border']};
            border-top: 1px solid {p['btn_bevel_top']};
            border-bottom: 2px solid {p['btn_bevel_bottom']};
            border-radius: 4px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                         stop:0 {p['btn_hover_top']},
                         stop:1 {p['btn_hover_bottom']});
            border: 1px solid {p['accent']};
            border-top: 1px solid {p['accent_hover']};
            color: #ffffff;
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                         stop:0 {p['btn_pressed_top']},
                         stop:1 {p['btn_pressed_bottom']});
            border: 1px solid {p['btn_bevel_bottom']};
            padding-top: 5px;
            padding-bottom: 3px;
        }}
        """

    # ---- window plumbing -------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def _start_drag(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _do_drag(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def _end_drag(self, event):
        self._drag_pos = None
