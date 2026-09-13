#!/usr/bin/env python3
"""Symphony — a classic-Winamp-style desktop music player.

Run with:  python main.py
See README.md for setup (LibVLC install, plugin credentials).
"""
import sys

from PyQt5.QtWidgets import QApplication

from symphony import config as cfgmod
from symphony.ui.main_window import MainWindow
from symphony.ui import theme as theme_mod


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Symphony")
    cfg = cfgmod.load()
    app.setStyleSheet(theme_mod.app_stylesheet(
        cfg.get("theme", "dark"), cfg.get("ui_font_family", ""), cfg.get("ui_font_size", 11)))

    window = MainWindow()
    window.move(120, 120)
    window.show()

    # Position the EQ/Playlist windows near the main window, but leave them
    # closed on startup — the player shouldn't open with extra windows
    # cluttering the screen. Use Options → or the EQ/PLAYLIST buttons.
    window.eq_window.move(window.x() + 285, window.y())
    window.playlist_window.move(window.x(), window.y() + 210)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
