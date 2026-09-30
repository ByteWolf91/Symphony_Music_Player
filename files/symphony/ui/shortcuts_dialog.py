from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QWidget, QFrame)

from symphony.ui import theme as theme_mod

# (key, action) — matches the classic shortcut layout, adapted to Symphony.
SHORTCUTS = [
    ("Space", "Play / Pause"),
    ("N", "Skip to next track"),
    ("B", "Skip to previous track"),
    ("F", "Seek forward 10s"),
    ("D", "Seek backward 10s"),
    ("S", "Toggle shuffle"),
    ("R", "Toggle repeat (wrap playlist)"),
    ("+ / =", "Volume up"),
    ("-", "Volume down"),
    ("M", "Choose music folder"),
    ("Enter", "Play the selected song in the list"),
    ("Up / Down", "Move selection in the song list"),
    ("Page Up / Down", "Move selection a page at a time"),
    ("Ctrl+E", "Show / hide Equalizer"),
    ("Ctrl+L", "Show / hide Playlist"),
    ("Ctrl+Left / Right", "Adjust balance"),
    ("Delete", "Remove selected track from playlist"),
    ("Q", "Quit"),
]


class ShortcutsDialog(QDialog):
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(460, 480)
        font_family = config.get("ui_font_family", "") if config else ""
        font_size = config.get("ui_font_size", 11) if config else 11
        self.setStyleSheet(theme_mod.readable_dialog_qss(font_family, font_size) + """
            QDialog { background: #14161e; }
        """)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(4)

        heading = QLabel("Keyboard Shortcuts")
        heading.setStyleSheet("font-size:19px; font-weight:800; color:#ffffff;")
        root.addWidget(heading)

        subtitle = QLabel("Symphony player controls")
        subtitle.setStyleSheet("color:#9aa4bd; font-size:12px;")
        root.addWidget(subtitle)
        root.addSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        # The scroll area's viewport otherwise paints the system's default
        # (often white) base color, making the light text unreadable.
        scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget "
            "{ background: #14161e; border: none; }")
        inner = QWidget()
        inner.setStyleSheet("background: #14161e;")
        rows = QVBoxLayout(inner)
        rows.setSpacing(8)
        rows.setContentsMargins(0, 0, 0, 0)

        for key, action in SHORTCUTS:
            row = QHBoxLayout()
            row.setSpacing(14)

            key_label = QLabel(key)
            key_label.setFixedWidth(140)
            key_label.setAlignment(Qt.AlignCenter)
            key_label.setStyleSheet("""
                QLabel {
                    background: #2b3040;
                    color: #bfe9c0;
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                    font-size: 12px;
                    border: 1px solid #454c60;
                    border-radius: 4px;
                    padding: 6px 8px;
                }
            """)
            action_label = QLabel(action)
            action_label.setStyleSheet("color:#eef0f8; font-size:13px;")
            action_label.setWordWrap(True)

            row.addWidget(key_label)
            row.addWidget(action_label, 1)
            rows.addLayout(row)

        rows.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)
