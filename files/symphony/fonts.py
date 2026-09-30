"""Custom font support: register .ttf/.otf/.ttc files with Qt so they can be
picked in Preferences like any installed font. Paths are remembered in the
config ("custom_font_files") and re-registered on every launch."""
import os

from PyQt5.QtGui import QFontDatabase

FONT_FILE_FILTER = "Fonts (*.ttf *.otf *.ttc *.otc);;All files (*)"


def register_font_file(path):
    """Register one font file; returns the family names it provides."""
    if not os.path.isfile(path):
        return []
    font_id = QFontDatabase.addApplicationFont(path)
    if font_id == -1:
        return []
    return QFontDatabase.applicationFontFamilies(font_id)


def load_saved_fonts(paths):
    """Register every remembered font file that still exists."""
    for path in paths or []:
        register_font_file(path)
