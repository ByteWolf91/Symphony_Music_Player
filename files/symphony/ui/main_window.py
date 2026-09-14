import os

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QKeySequence, QPainter, QIcon, QColor
from PyQt5.QtWidgets import (
    QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMenu, QShortcut, QMessageBox, QDialog, QSplitter,
    QApplication, QStyle
)

from symphony import config as cfgmod
from symphony.core.player import PlayerEngine
from symphony.core.playlist import Playlist, Track
from symphony.core.skin import WszSkin
from symphony.core import skin as skin_mod
from symphony.core import metadata as metadata_mod
from symphony.core import playlist_io
from symphony.core import cdrom as cdrom_mod
from symphony.ui.widgets import LCDDigits, Visualizer, TitleScroller, WheelSlider
from symphony.ui.eq_window import EqWindow
from symphony.ui.playlist_window import PlaylistWindow
from symphony.ui.radio_dialog import RadioDialog
from symphony.ui.preferences_dialog import PreferencesDialog
from symphony.ui.shortcuts_dialog import ShortcutsDialog
from symphony.ui.youtube_dialog import YouTubeDownloadDialog
from symphony.ui import theme as theme_mod

AUDIO_EXTENSIONS = (
    "Audio files (*.mp3 *.wav *.flac *.ogg *.oga *.opus *.m4a *.aac *.wma "
    "*.ape *.aiff *.aif *.mid *.mod *.xm *.it *.s3m);;All files (*)"
)
AUDIO_SUFFIXES = {
    ".mp3", ".wav", ".flac", ".ogg", ".oga", ".opus", ".m4a", ".aac",
    ".wma", ".ape", ".aiff", ".aif", ".mid", ".mod", ".xm", ".it", ".s3m"
}
PLAYLIST_FILTER = "Symphony playlist (*.sympl);;M3U playlist (*.m3u *.m3u8);;All files (*)"


def fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


class MainWindow(QWidget):
    def __init__(self):
        # Native window chrome gives us proper edge/corner resizing.
        super().__init__(None, Qt.Window)

        self.config = cfgmod.load()
        self.skin = WszSkin()
        self.player = PlayerEngine()
        self.playlist = Playlist()
        self._seek_dragging = False
        self._seek_hold_timer = None
        self._seek_hold_amount = 5
        self._theme = self.config.get("theme", "dark")

        self.setWindowTitle("Symphony")
        self.setMinimumSize(420, 300)
        self.resize(560, 390)
        self.setAcceptDrops(True)
        if self.config.get("always_on_top", False):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.eq_window = EqWindow(
            self.player, lambda: self.skin, self._theme,
            self.config.get("ui_font_family", ""),
            self.config.get("ui_font_size", 11),
        )
        self.playlist_window = PlaylistWindow(
            font_family=self.config.get("ui_font_family", ""),
            font_size=self.config.get("ui_font_size", 11),
        )
        self.radio_dialog = RadioDialog(self.config)
        self.youtube_dialog = None

        self._build_ui()
        self._wire_signals()
        self._register_shortcuts()

        volume = self.config.get("volume", 80)
        self.player.set_volume(volume)
        self.vol_slider.setValue(volume)
        self._on_volume_changed(volume)
        self.btn_shuffle.setChecked(self.config.get("shuffle", False))
        self.btn_repeat.setChecked(self.config.get("repeat", False))

        self._resolve_startup_skin()
        self.eq_window.load_values(
            enabled=self.config.get("eq_enabled", False),
            preamp=self.config.get("eq_preamp", 0),
            bands=self.config.get("eq_bands", [0] * 10),
            preset=self.config.get("eq_preset", "Flat"),
        )

    def _resolve_startup_skin(self):
        """Pick the skin to show on launch: the user's last-loaded skin if
        "restore last skin" is enabled and it still exists, otherwise stay
        unskinned so the app's own dark/green theme (buttons, sliders, LCD
        panel) is what's actually visible out of the box.

        A previous build of this app auto-selected and *persisted* the
        bundled classic Winamp skin (base-2.91) as "last_skin_path" the
        first time it ever ran. That means anyone who ran that build even
        once has a config file that still points at it, so simply removing
        the auto-load call isn't enough — we also have to stop treating
        that particular stale, auto-assigned path as if it were a real user
        choice, or the classic skin (with its own baked-in "kbps"/"kHz"
        text and tiny sprite buttons/backgrounds, all of which clash with
        the app's real theme) keeps coming back from old config files.
        A skin the user picks explicitly via Options → Load Skin is always
        respected."""
        last_skin = self.config.get("last_skin_path", "")
        bundled_default = skin_mod.default_skin_path()
        is_stale_bundled_default = bool(last_skin) and os.path.abspath(last_skin) == os.path.abspath(bundled_default)
        if is_stale_bundled_default:
            self.config["last_skin_path"] = ""
            cfgmod.save(self.config)
            return
        if self.config.get("restore_skin", True) and last_skin and os.path.isfile(last_skin):
            skin = WszSkin.load(last_skin)
            if skin.loaded:
                self.skin = skin
                self._apply_skin_controls()


    def disable_skin(self):
        self.skin = None
        self.config['last_skin_path'] = ''
        self._skin_color_cache = {}
        theme = self.config.get('theme', 'dark')
        self.apply_theme(theme)
        self._apply_skin_controls()
        if hasattr(self, 'playlist_window') and self.playlist_window:
            self.playlist_window.apply_skin(None)
        if hasattr(self, 'eq_window') and self.eq_window:
            self.eq_window.apply_skin(None)
        self.status_bar.showMessage('Skin disabled. Using default theme.', 3000)

    def _apply_skin_controls(self):
        controls = (
            ("previous", getattr(self, "btn_prev", None), "|◄◄"),
            ("play", getattr(self, "btn_play", None), "▶"),
            ("pause", getattr(self, "btn_pause", None), "❚❚"),
            ("stop", getattr(self, "btn_stop", None), "■"),
            ("next", getattr(self, "btn_next", None), "►►|"),
            ("eject", getattr(self, "btn_eject", None), "ADD"),
        )
        for name, button, fallback in controls:
            if button is not None:
                button.setIcon(QIcon())
                button.setText(fallback)
        toggle_controls = (
            ("shuffle", getattr(self, "btn_shuffle", None), "SHUFFLE"),
            ("repeat", getattr(self, "btn_repeat", None), "REPEAT"),
            ("eq", getattr(self, "btn_eq", None), "EQ"),
            ("playlist", getattr(self, "btn_pl", None), "PLAYLIST"),
        )
        for name, button, fallback in toggle_controls:
            if button is not None:
                button.setIcon(QIcon())
                button.setText(fallback)
        if hasattr(self, "playlist_window"):
            self.playlist_window.set_skin(self.skin)
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        title = QHBoxLayout()
        title_label = QLabel("SYMPHONY")
        title_label.setStyleSheet("font-weight:bold; letter-spacing:2px;")
        options_btn = QPushButton("OPTIONS")
        options_btn.clicked.connect(self._show_options_menu)
        title.addWidget(title_label)
        title.addStretch()
        title.addWidget(options_btn)
        root.addLayout(title)

        # The "now playing" display and the transport controls live in a
        # vertical splitter so the display can be resized (dragged smaller
        # or larger) independently of the rest of the window, instead of
        # permanently eating a big fixed chunk of the skin.
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(6)
        self.splitter.setChildrenCollapsible(False)

        screen = QWidget()
        screen.setMinimumHeight(46)
        screen.setStyleSheet(f"QWidget {{ background: {theme_mod.palette(self._theme)['panel']}; border: 1px solid {theme_mod.palette(self._theme)['border']}; border-radius: 8px; }}")
        screen_layout = QVBoxLayout(screen)
        screen_layout.setContentsMargins(10, 6, 10, 6)
        screen_layout.setSpacing(2)

        row1 = QHBoxLayout()
        self.clock = LCDDigits(lambda: self.skin)
        self.viz = Visualizer(lambda: self.skin)
        row1.addWidget(self.clock)
        row1.addStretch()
        row1.addWidget(self.viz)
        screen_layout.addLayout(row1)

        self.title_scroller = TitleScroller()
        self.title_scroller.set_text(
            "Symphony — drop files here, or use Options → Add Files / Add Folder"
        )
        screen_layout.addWidget(self.title_scroller)

        # Artist / genre now-playing line (item 7).
        self.artist_genre_label = QLabel("")
        self.artist_genre_label.setStyleSheet(
            "color:#8891a5; font-size:11px; font-weight:500;")
        screen_layout.addWidget(self.artist_genre_label)

        # Duration / seek bar lives right in the LCD "screen" panel, directly
        # under the now-playing text, instead of buried at the top of the
        # resizable controls column below — this is the single most-used
        # control after play/pause, so it gets the most prominent spot and a
        # much bigger, high-contrast bar + bold digit-style time readout.
        seek_row = QHBoxLayout()
        seek_row.setSpacing(8)
        self.time_current_label = QLabel("00:00")
        self.time_total_label = QLabel("00:00")
        for lab in (self.time_current_label, self.time_total_label):
            lab.setStyleSheet(
                "font-size:11px; font-weight:500; color:#8891a5;"
            )
            lab.setMinimumWidth(38)
        self.time_current_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.time_total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.seek_slider = WheelSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setMinimumHeight(22)
        self.seek_slider.setToolTip("Seek: 00:00 / 00:00  (scroll to seek)")
        self.seek_slider.setStyleSheet(theme_mod.seek_bar_qss(self._theme))
        seek_row.addWidget(self.time_current_label)
        seek_row.addWidget(self.seek_slider, 1)
        seek_row.addWidget(self.time_total_label)
        screen_layout.addLayout(seek_row)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        # No standalone "VOLUME" text label — the slider plus a compact
        # icon+percentage chip is enough. The bar is kept short and hugs the
        # left edge (rather than stretching across the whole width) so it
        # reads as one tidy control instead of a stray oversized bar.
        vb_row = QHBoxLayout()
        vb_row.setSpacing(8)
        self.vol_slider = WheelSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setFixedHeight(16)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setToolTip("Volume: 80%  (scroll to adjust)")
        self.vol_slider.setStyleSheet(theme_mod.volume_slider_qss(self._theme))
        self.vol_value_label = QLabel("🔊 80%")
        self.vol_value_label.setAlignment(Qt.AlignCenter)
        self.vol_value_label.setFixedWidth(58)
        self.vol_value_label.setStyleSheet(theme_mod.volume_value_label_qss(self._theme))
        vb_row.addWidget(self.vol_slider)
        vb_row.addWidget(self.vol_value_label)
        vb_row.addStretch(1)
        controls_layout.addLayout(vb_row)

        transport_wrap = QWidget()
        transport_wrap.setObjectName("transport_wrap")
        transport = QHBoxLayout(transport_wrap)
        transport.setContentsMargins(0, 0, 0, 0)
        transport.setSpacing(6)
        self.btn_prev = QPushButton()
        self.btn_seek_back = QPushButton()
        self.btn_play = QPushButton()
        self.btn_pause = QPushButton()
        self.btn_stop = QPushButton()
        self.btn_seek_fwd = QPushButton()
        self.btn_next = QPushButton()
        self.btn_eject = QPushButton()
        # One consistent icon-button treatment for the whole row (instead of
        # a mix of plain text labels and icons), so it reads as one unit.
        icon_map = (
            (self.btn_prev, QStyle.SP_MediaSkipBackward, "Previous track"),
            (self.btn_seek_back, QStyle.SP_MediaSeekBackward,
             "Seek back — tap for 5s, hold to ramp up to 10s"),
            (self.btn_play, QStyle.SP_MediaPlay, "Play"),
            (self.btn_pause, QStyle.SP_MediaPause, "Pause"),
            (self.btn_stop, QStyle.SP_MediaStop, "Stop"),
            (self.btn_seek_fwd, QStyle.SP_MediaSeekForward,
             "Seek forward — tap for 5s, hold to ramp up to 10s"),
            (self.btn_next, QStyle.SP_MediaSkipForward, "Next track"),
            (self.btn_eject, QStyle.SP_DialogOpenButton, "Add files"),
        )
        for b, std_icon, tip in icon_map:
            b.setIcon(self.style().standardIcon(std_icon))
            b.setIconSize(QSize(17, 17))
            b.setToolTip(tip)
                # Hide seek buttons to display 6 clean, wide transport buttons
        self.btn_seek_back.hide()
        self.btn_seek_fwd.hide()
        for b in (self.btn_prev, self.btn_pause, self.btn_stop, self.btn_next, self.btn_eject):
            b.setMinimumHeight(34)
            b.setMinimumWidth(72)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setObjectName("transport_button")
            transport.addWidget(b)
        self.btn_play.setMinimumHeight(34)
        self.btn_play.setMinimumWidth(80)
        self.btn_play.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_play.setObjectName("transport_button")
        transport.insertWidget(0, self.btn_prev)
        transport.insertWidget(1, self.btn_play)
        transport.insertWidget(2, self.btn_pause)
        transport.insertWidget(3, self.btn_stop)
        transport.insertWidget(4, self.btn_next)
        transport.insertWidget(5, self.btn_eject)
        # Play is the primary action, so it gets its own object name to pick
        # up the filled/pill treatment in transport_button_qss instead of
        # blending into the rest of the row.
        self.btn_play.setObjectName("transport_button_play")
        transport_wrap.setStyleSheet(theme_mod.transport_button_qss(self._theme))
        controls_layout.addWidget(transport_wrap)

        toggles_wrap = QWidget()
        toggles_wrap.setObjectName("toggles_wrap")
        toggles = QHBoxLayout(toggles_wrap)
        toggles.setContentsMargins(0, 0, 0, 0)
        self.btn_shuffle = QPushButton("SHUFFLE")
        self.btn_repeat = QPushButton("REPEAT")
        self.btn_eq = QPushButton("EQ")
        self.btn_pl = QPushButton("PLAYLIST")
        for b in (self.btn_shuffle, self.btn_repeat, self.btn_eq, self.btn_pl):
            b.setCheckable(True)
            b.setFixedHeight(24)
            b.setObjectName("toggle_button")
            b.setFixedHeight(24)
            b.setObjectName("toggle_button")
            b.setFixedHeight(24)
            b.setObjectName("toggle_button")
            b.setFixedHeight(24)
            b.setObjectName("toggle_button")
            b.setMinimumHeight(28)
            b.setObjectName("toggle_btn")
            b.setStyleSheet(theme_mod.transport_button_qss(self._theme))
            toggles.addWidget(b)
        toggles_wrap.setStyleSheet(theme_mod.eq_toggle_qss(self._theme))
        controls_layout.addWidget(toggles_wrap)

        self.splitter.addWidget(screen)
        self.splitter.addWidget(controls)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        start_h = int(self.config.get("now_playing_height", 70))
        self.splitter.setSizes([start_h, 260])
        root.addWidget(self.splitter, 1)

    def _small_label(self, text):
        lab = QLabel(text)
        lab.setStyleSheet("font-size:9px; font-weight:bold;")
        return lab

    # ---------------- skin painting ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.skin.loaded:
            bg = self.skin.main_background()
            if bg and not bg.isNull():
                painter.drawPixmap(self.rect(), bg)
            else:
                painter.fillRect(self.rect(), QColor(theme_mod.palette(self._theme)["bg"]))
        else:
            # self.palette().window() is Qt's generic system color (often a
            # light gray) and has nothing to do with the app's own dark/
            # green theme, so unskinned windows used to show a mismatched
            # background block behind the controls. Paint the actual theme
            # background instead so it's coherent everywhere.
            painter.fillRect(self.rect(), QColor(theme_mod.palette(self._theme)["bg"]))
        painter.end()

    # ---------------- wiring ----------------
    def _wire_signals(self):
        self.btn_play.clicked.connect(self.play_current)
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_stop.clicked.connect(self.player.stop)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_eject.clicked.connect(self.add_files_dialog)
        self.btn_seek_back.pressed.connect(lambda: self._start_seek_hold(-1))
        self.btn_seek_back.released.connect(self._stop_seek_hold)
        self.btn_seek_fwd.pressed.connect(lambda: self._start_seek_hold(1))
        self.btn_seek_fwd.released.connect(self._stop_seek_hold)

        self.btn_shuffle.toggled.connect(lambda v: setattr(self.playlist, "shuffle", v))
        self.btn_repeat.toggled.connect(lambda v: setattr(self.playlist, "repeat", v))
        self.btn_shuffle.toggled.connect(lambda: self._apply_skin_controls())
        self.btn_repeat.toggled.connect(lambda: self._apply_skin_controls())
        self.btn_eq.toggled.connect(self.eq_window.setVisible)
        self.btn_pl.toggled.connect(self.playlist_window.setVisible)
        self.btn_eq.toggled.connect(lambda: self._apply_skin_controls())
        self.btn_pl.toggled.connect(lambda: self._apply_skin_controls())
        # Keep the toggle buttons in sync even when a satellite window is
        # closed via its own titlebar (×) button, so one click reopens it.
        self.eq_window.visibility_changed.connect(self.btn_eq.setChecked)
        self.playlist_window.visibility_changed.connect(self.btn_pl.setChecked)

        self.vol_slider.valueChanged.connect(self.player.set_volume)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        self.vol_slider.wheel_scrolled.connect(
            lambda steps: self.vol_slider.setValue(
                max(0, min(100, self.vol_slider.value() + steps * 5))))
        self.seek_slider.sliderPressed.connect(lambda: setattr(self, "_seek_dragging", True))
        self.seek_slider.sliderReleased.connect(self._on_seek_released)
        self.seek_slider.wheel_scrolled.connect(
            lambda steps: self.player.seek_relative(steps * 5))

        self.player.position_changed.connect(self._on_position_changed)
        self.player.state_changed.connect(self._on_state_changed)
        self.player.track_ended.connect(self._on_track_ended)

        self.playlist_window.play_index_requested.connect(self.load_track)
        self.playlist_window.remove_index_requested.connect(self._remove_track)
        self.playlist_window.clear_requested.connect(self._clear_playlist)
        self.playlist_window.sort_requested.connect(self._sort_playlist)
        self.playlist_window.dedupe_requested.connect(self._remove_duplicate_tracks)
        self.playlist_window.add_files_requested.connect(self.add_files_dialog)
        self.playlist_window.add_folder_requested.connect(self.add_folder_dialog)
        self.playlist_window.add_cd_requested.connect(self.select_cd_drive_dialog)
        self.playlist_window.youtube_download_requested.connect(
            self.show_youtube_download_dialog)
        self.playlist_window.radio_favorites_requested.connect(self.radio_dialog.show_favorites)
        self.playlist_window.save_playlist_requested.connect(self.save_playlist_dialog)
        self.playlist_window.load_playlist_requested.connect(self.load_playlist_dialog)

        self.radio_dialog.station_chosen.connect(
            lambda name, url: self._on_plugin_track_chosen("radio", name, url))

    def _register_shortcuts(self):
        bindings = {
            "Space": self.toggle_play_pause,
            "N": self.next_track,
            "B": self.prev_track,
            "F": lambda: self.player.seek_relative(10),
            "D": lambda: self.player.seek_relative(-10),
            "S": self.btn_shuffle.toggle,
            "R": self.btn_repeat.toggle,
            "+": lambda: self.vol_slider.setValue(min(100, self.vol_slider.value() + 5)),
            "=": lambda: self.vol_slider.setValue(min(100, self.vol_slider.value() + 5)),
            "-": lambda: self.vol_slider.setValue(max(0, self.vol_slider.value() - 5)),
            "M": self.add_folder_dialog,
            "Q": self.close,
            "Ctrl+E": self.btn_eq.toggle,
            "Ctrl+L": self.btn_pl.toggle,
            "Delete": lambda: self._remove_track(self.playlist_window.selected_index()),
        }
        for seq, fn in bindings.items():
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(fn)

    # ---------------- options menu ----------------
    def _show_options_menu(self):
        menu = QMenu(self)
        palette = theme_mod.palette(self._theme)
        menu_qss = theme_mod.readable_dialog_qss(
            self.config.get("ui_font_family", ""),
            self.config.get("ui_font_size", 11),
        ) + f"""
            QMenu {{ background: {palette['panel']}; border: 1px solid {palette['border']}; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px 8px 16px; border-radius: 3px; color: {palette['text']}; }}
            QMenu::item:selected {{ background: {palette['accent']}; color: #10120f; }}
            QMenu::separator {{ height: 1px; background: {palette['border']}; margin: 5px 6px; }}
        """
        menu.setStyleSheet(menu_qss)
        menu.addAction("Add Files…", self.add_files_dialog)
        menu.addAction("Add Folder…", self.add_folder_dialog)
        menu.addSeparator()
        menu.addAction("Save Playlist…", self.save_playlist_dialog)
        menu.addAction("Load Playlist…", self.load_playlist_dialog)
        menu.addSeparator()
        menu.addAction("Load Skin (.wsz)…", self.load_skin_dialog)
        menu.addAction("Disable Skin (Use Default Theme)", self._disable_skin)
        menu.addSeparator()
        menu.addAction("Internet Radio…", self.radio_dialog.show)
        menu.addSeparator()
        menu.addAction("Preferences…", self.show_preferences_dialog)
        menu.addAction("Keyboard Shortcuts…", self._show_shortcuts_dialog)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomLeft())
                   if self.sender() else self.mapToGlobal(self.rect().topRight()))

    def show_preferences_dialog(self):
        dlg = PreferencesDialog(self.config, self)
        if dlg.exec_() == QDialog.Accepted:
            dlg.save()
            cfgmod.save(self.config)
            self._apply_theme(self.config.get("theme", "dark"))
            self.setWindowFlag(Qt.WindowStaysOnTopHint, self.config.get("always_on_top", False))
            self.show()
            self._update_now_playing_label()

    def _show_shortcuts_dialog(self):
        dlg = ShortcutsDialog(self.config, self)
        dlg.exec_()

    def _apply_theme(self, theme_name):
        self._theme = theme_name
        font_family = self.config.get("ui_font_family", "")
        font_size = self.config.get("ui_font_size", 11)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme_mod.app_stylesheet(theme_name, font_family, font_size))
        self.eq_window.set_theme(theme_name)
        self.eq_window.set_font(font_family, font_size)
        self.playlist_window.set_font(font_family, font_size)
        self.playlist_window.set_skin(self.skin)
        for w in self.findChildren(QWidget):
            if w.objectName() == "transport_wrap":
                w.setStyleSheet(theme_mod.transport_button_qss(theme_name))
            elif w.objectName() == "toggles_wrap":
                w.setStyleSheet(theme_mod.eq_toggle_qss(theme_name))
        self.seek_slider.setStyleSheet(theme_mod.seek_bar_qss(theme_name))
        self.vol_slider.setStyleSheet(theme_mod.volume_slider_qss(theme_name))
        self.vol_value_label.setStyleSheet(theme_mod.volume_value_label_qss(theme_name))
        dlg_qss = theme_mod.readable_dialog_qss(font_family, font_size)
        for dlg in (self.radio_dialog,):
            dlg.setStyleSheet(dlg_qss)
        self.update()

    # ---------------- file / folder / skin loading ----------------
    def _add_paths(self, paths):
        paths = [os.path.abspath(p) for p in paths if os.path.isfile(p)]
        if not paths:
            return

        read_tags = self.config.get("read_tags", True)
        start_len = len(self.playlist.tracks)
        for p in paths:
            fallback_title = os.path.splitext(os.path.basename(p))[0]
            if read_tags:
                tags = metadata_mod.read_tags(p, fallback_title)
                self.playlist.add(Track(
                    title=tags.title, source="local", uri=p,
                    duration=tags.duration, artist=tags.artist, genre=tags.genre,
                    bitrate=tags.bitrate, sample_rate=tags.sample_rate,
                ))
            else:
                self.playlist.add(Track(title=fallback_title, source="local", uri=p))
        self._refresh_playlist_window()

        if self.playlist.current_index == -1:
            self.load_track(
                start_len,
                autoplay=self.config.get("autoplay_import", True)
            )

    def add_files_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add music files", "", AUDIO_EXTENSIONS
        )
        self._add_paths(paths)

    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Import music folder", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if not folder:
            return

        files = []
        if self.config.get("scan_subfolders", True):
            for base, _, names in os.walk(folder):
                for name in names:
                    if os.path.splitext(name)[1].lower() in AUDIO_SUFFIXES:
                        files.append(os.path.join(base, name))
        else:
            for name in os.listdir(folder):
                p = os.path.join(folder, name)
                if os.path.isfile(p) and os.path.splitext(name)[1].lower() in AUDIO_SUFFIXES:
                    files.append(p)

        files.sort(key=lambda p: p.lower())
        if not files:
            QMessageBox.information(
                self, "No music found",
                "There were no supported audio files in that folder."
            )
            return
        self._add_paths(files)

    def select_cd_drive_dialog(self):
        """Choose one optical drive/device and add its tracks to the playlist.

        There is intentionally one CD path now: no auto-detect, play-now
        duplicate, or manual path prompt. The file dialog is the same simple
        drive selector on all supported desktop platforms.
        """
        start_dir = cdrom_mod.browse_start_dir()
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CD Drive", start_dir, "All files (*)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not path:
            return

        tracks = self._read_cd_tracks(path)
        if not tracks:
            QMessageBox.warning(
                self, "No audio CD found",
                f"Couldn't read any tracks from \"{path}\". Make sure "
                "that's the right drive/device and an audio CD is "
                "inserted."
            )
            return
        self._add_cd_tracks(tracks)

    def _read_cd_tracks(self, drive):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            return cdrom_mod.read_tracks(drive)
        finally:
            QApplication.restoreOverrideCursor()

    def _add_cd_tracks(self, tracks):
        start_len = len(self.playlist.tracks)
        for t in tracks:
            self.playlist.add(Track(
                title=f"Audio CD — Track {t.index:02d}",
                source="cd", uri=t.uri,
                duration=t.duration or None,
            ))
        self._refresh_playlist_window()
        if self.playlist.current_index == -1:
            self.load_track(start_len, autoplay=self.config.get("autoplay_import", True))

    def show_youtube_download_dialog(self):
        if self.youtube_dialog is not None and self.youtube_dialog.isVisible():
            self.youtube_dialog.raise_()
            self.youtube_dialog.activateWindow()
            return
        self.youtube_dialog = YouTubeDownloadDialog(self)
        self.youtube_dialog.files_ready.connect(self._add_downloaded_files)
        self.youtube_dialog.setStyleSheet(theme_mod.readable_dialog_qss(
            self.config.get("ui_font_family", ""),
            self.config.get("ui_font_size", 11),
        ))
        self.youtube_dialog.show()

    def _add_downloaded_files(self, paths):
        self._add_paths(paths)

    def save_playlist_dialog(self):
        if not self.playlist.tracks:
            QMessageBox.information(self, "Nothing to save", "The playlist is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save playlist", "playlist.sympl", PLAYLIST_FILTER
        )
        if not path:
            return
        try:
            playlist_io.save_playlist(path, self.playlist.tracks)
        except OSError as e:
            QMessageBox.warning(self, "Save failed", str(e))

    def load_playlist_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load playlist", "", PLAYLIST_FILTER
        )
        if not path:
            return
        try:
            tracks = playlist_io.load_playlist(path)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Load failed", str(e))
            return
        if not tracks:
            QMessageBox.information(self, "Empty playlist", "That playlist had no tracks.")
            return
        start_len = len(self.playlist.tracks)
        for t in tracks:
            self.playlist.add(t)
        self._refresh_playlist_window()
        if self.playlist.current_index == -1:
            self.load_track(start_len, autoplay=self.config.get("autoplay_import", True))

    def load_skin_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Winamp skin", "",
            "Winamp skins (*.wsz *.zip);;All files (*)"
        )
        if not path:
            return

        skin = WszSkin.load(path)
        if not skin.loaded:
            QMessageBox.warning(
                self, "Skin load failed",
                "Couldn't find a usable main.bmp inside that file. "
                "This player currently supports classic Winamp 2.x skins."
            )
            return

        self.skin = skin
        self.config["last_skin_path"] = path
        cfgmod.save(self.config)
        self.update()
        self._apply_skin_controls()
        self.eq_window.update()
        self.playlist_window.update()

    def _on_plugin_track_chosen(self, source, title, uri):
        self.playlist.add(Track(title=title, source=source, uri=uri))
        self._refresh_playlist_window()
        if self.playlist.current_index == -1:
            self.load_track(
                len(self.playlist.tracks) - 1,
                autoplay=self.config.get("autoplay_import", True)
            )

    # ---------------- transport ----------------
    def load_track(self, index, autoplay=True):
        if index is None or not (0 <= index < len(self.playlist.tracks)):
            return
        self.playlist.current_index = index
        track = self.playlist.tracks[index]
        self.player.load(track.uri)
        self.title_scroller.set_text(f"{track.title} — Symphony")
        self._update_now_playing_label()
        self._refresh_playlist_window()
        if autoplay:
            self.play_current()

    def _update_now_playing_label(self):
        track = self.playlist.current()
        if not track:
            self.artist_genre_label.setText("")
            return
        parts = []
        if self.config.get("show_artist_genre", True):
            if track.artist:
                parts.append(f"Artist: {track.artist}")
            if track.genre:
                parts.append(f"Genre: {track.genre}")
        self.artist_genre_label.setText("   ".join(parts))

    def toggle_play_pause(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.play_current()

    def play_current(self):
        if self.playlist.current_index == -1 and self.playlist.tracks:
            self.load_track(0, autoplay=True)
            return
        self.player.play()

    def next_track(self):
        idx = self.playlist.next_index()
        self.load_track(idx)

    def prev_track(self):
        idx = self.playlist.prev_index()
        self.load_track(idx)

    def _on_track_ended(self):
        if self.playlist.repeat:
            self.player.seek_seconds(0)
            self.player.play()
        elif self.playlist.tracks:
            self.next_track()

    def _remove_track(self, index):
        self.playlist.remove(index)
        self._refresh_playlist_window()

    def _clear_playlist(self):
        if self.config.get("confirm_clear", True) and self.playlist.tracks:
            reply = QMessageBox.question(
                self, "Clear playlist", "Clear the entire playlist?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.player.stop()
        self.playlist.clear()
        self._refresh_playlist_window()

    def _sort_playlist(self):
        self.playlist.sort_by_title()
        self._refresh_playlist_window()

    def _remove_duplicate_tracks(self):
        """Keep the first occurrence of each source/URI pair."""
        current = self.playlist.current()
        current_key = (current.source, current.uri) if current else None
        seen = set()
        unique = []
        for track in self.playlist.tracks:
            key = (track.source, track.uri)
            if key in seen:
                continue
            seen.add(key)
            unique.append(track)
        self.playlist.tracks = unique
        self.playlist.current_index = next(
            (i for i, track in enumerate(unique)
             if (track.source, track.uri) == current_key),
            -1,
        )
        self._refresh_playlist_window()

    def _refresh_playlist_window(self):
        self.playlist_window.refresh(
            self.playlist.tracks,
            self.playlist.current_index,
            self.playlist.total_duration()
        )

    # ---------------- player feedback ----------------
    def _on_position_changed(self, current, duration):
        self.clock.set_text(fmt_time(current))
        self.time_current_label.setText(fmt_time(current))
        if duration > 0:
            self.time_total_label.setText(fmt_time(duration))
        if not self._seek_dragging and duration > 0:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int((current / duration) * 1000))
            self.seek_slider.blockSignals(False)
        self.seek_slider.setToolTip(f"{fmt_time(current)} / {fmt_time(duration)}  (scroll to seek)")

    def _on_volume_changed(self, value):
        """Keep the volume chip's icon+percentage in sync — the icon alone
        reflects the current level at a glance (muted / low / high) without
        needing a separate text label."""
        icon = "🔇" if value == 0 else ("🔈" if value < 50 else "🔊")
        self.vol_value_label.setText(f"{icon} {value}%")
        self.vol_slider.setToolTip(f"Volume: {value}%  (scroll to adjust)")

    def _on_state_changed(self, state):
        self.viz.set_playing(state == "playing")

    def _on_seek_released(self):
        duration = self.player.get_length_seconds()
        if duration > 0:
            frac = self.seek_slider.value() / 1000.0
            self.player.seek_seconds(frac * duration)
        self._seek_dragging = False

    # ---------------- seek buttons (tap = 5s, hold ramps to 10s) ----------------
    def _start_seek_hold(self, direction):
        """A quick tap seeks 5s. Keep the button held down and each
        subsequent tick seeks a bit further, ramping up to a 10s cap, so a
        quick tap stays a small nudge while a longer hold covers more
        ground without needing repeated clicks."""
        self._seek_hold_amount = 5
        self.player.seek_relative(direction * self._seek_hold_amount)
        self._seek_hold_timer = QTimer(self)
        self._seek_hold_timer.setInterval(350)
        self._seek_hold_timer.timeout.connect(lambda: self._seek_hold_tick(direction))
        self._seek_hold_timer.start()

    def _seek_hold_tick(self, direction):
        self._seek_hold_amount = min(10, self._seek_hold_amount + 1)
        self.player.seek_relative(direction * self._seek_hold_amount)

    def _stop_seek_hold(self):
        if self._seek_hold_timer is not None:
            self._seek_hold_timer.stop()
            self._seek_hold_timer = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            p = url.toLocalFile()
            if os.path.isdir(p):
                # Dropped folders use the same import logic.
                if self.config.get("scan_subfolders", True):
                    for base, _, names in os.walk(p):
                        for name in names:
                            if os.path.splitext(name)[1].lower() in AUDIO_SUFFIXES:
                                paths.append(os.path.join(base, name))
                else:
                    paths.extend(
                        os.path.join(p, n) for n in os.listdir(p)
                        if os.path.isfile(os.path.join(p, n))
                        and os.path.splitext(n)[1].lower() in AUDIO_SUFFIXES
                    )
            elif os.path.splitext(p)[1].lower() in AUDIO_SUFFIXES:
                paths.append(p)
        self._add_paths(sorted(set(paths), key=lambda p: p.lower()))

    
    def _disable_skin(self):
        self.skin = WszSkin()
        self.config["last_skin_path"] = ""
        cfgmod.save(self.config)
        self._apply_skin_controls()
        self.setStyleSheet(theme_mod.app_stylesheet(
            self._theme,
            self.config.get("ui_font_family", ""),
            self.config.get("ui_font_size", 11)
        ))
        if hasattr(self, "playlist_window"):
            self.playlist_window.set_skin(self.skin)
        if hasattr(self, "eq_window"):
            self.eq_window.set_skin(self.skin)
        self.update()

    def closeEvent(self, event):
        if self.config.get("confirm_quit", False):
            reply = QMessageBox.question(
                self, "Quit Symphony", "Quit Symphony?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        if self.config.get("remember_volume", True):
            self.config["volume"] = self.vol_slider.value()
        self.config["shuffle"] = self.btn_shuffle.isChecked()
        self.config["repeat"] = self.btn_repeat.isChecked()
        eq_state = self.eq_window.snapshot()
        self.config["eq_enabled"] = eq_state["enabled"]
        self.config["eq_preset"] = eq_state["preset"]
        self.config["eq_preamp"] = eq_state["preamp"]
        self.config["eq_bands"] = eq_state["bands"]
        sizes = self.splitter.sizes()
        if sizes:
            self.config["now_playing_height"] = sizes[0]
        cfgmod.save(self.config)
        self.eq_window.close()
        self.playlist_window.close()
        self.radio_dialog.close()
        if self.youtube_dialog is not None:
            self.youtube_dialog.close()
        super().closeEvent(event)
