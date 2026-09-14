"""Light/dark theme stylesheets, classic Winamp-ish styling.

These apply on top of (and are skipped for) a loaded .wsz skin — a real
Winamp skin still takes priority for the main window's own paintEvent, but
the satellite windows (EQ, playlist, dialogs) and control widgets always use
this QSS so the whole app looks coherent even with no skin loaded.
"""

DARK = {
    "bg": "#171b24",
    "bg_alt": "#232936",
    "panel": "#10141c",
    "border": "#465166",
    "text": "#f4f7fb",
    "text_dim": "#aab6c8",
    "accent": "#6ee7a0",
    "accent_dim": "#214d3a",
}

LIGHT = {
    "bg": "#e7e9ee",
    "bg_alt": "#f4f5f8",
    "panel": "#ffffff",
    "border": "#b9bec9",
    "text": "#20232c",
    "text_dim": "#5a6070",
    "accent": "#2f8f2f",
    "accent_dim": "#bfe6bf",
}


def palette(theme_name: str) -> dict:
    return LIGHT if theme_name == "light" else DARK


def app_stylesheet(theme_name: str, font_family: str = "", font_size: int = 11) -> str:
    p = palette(theme_name)
    family = font_family.strip() or "Segoe UI, Noto Sans, sans-serif"
    size = max(8, min(24, int(font_size or 11)))
    menu_size = size + 1
    return f"""
    QWidget {{
        color: {p['text']};
        font-family: {family};
        font-size: {size}px;
    }}
    QDialog {{ background: {p['bg']}; }}
    QMainWindow {{ background: {p['bg']}; }}
    QToolTip {{
        background: {p['panel']}; color: {p['text']}; border: 1px solid {p['border']};
    }}
    QLineEdit, QComboBox, QListWidget, QSpinBox, QFontComboBox {{
        background: {p['panel']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 3px;
        padding: 3px;
    }}
    QListWidget::item:selected {{
        background: {p['accent_dim']};
        color: {p['text']};
    }}
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 {p['bg_alt']}, stop:1 {p['bg']});
        border: 1px solid {p['border']};
        border-radius: 4px;
        padding: 4px 10px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border: 1px solid {p['accent']};
    }}
    QPushButton:pressed {{
        background: {p['accent_dim']};
    }}
    QPushButton:checked {{
        background: {p['accent_dim']};
        border: 1px solid {p['accent']};
        color: {p['accent']};
    }}
    QMenu {{
        background: {p['panel']};
        color: {p['text']};
        border: 1px solid {p['border']};
        padding: 4px;
        font-size: {menu_size}px;
    }}
    QMenu::item {{
        padding: 7px 22px 7px 14px;
        border-radius: 3px;
    }}
    QMenu::item:selected {{
        background: {p['accent']};
        color: #10120f;
    }}
    QMenu::separator {{
        height: 1px;
        background: {p['border']};
        margin: 5px 6px;
    }}
    QTabWidget::pane {{
        border: 1px solid {p['border']};
        background: {p['panel']};
    }}
    QTabBar::tab {{
        background: {p['bg_alt']};
        color: {p['text']};
        padding: 6px 14px;
        border: 1px solid {p['border']};
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background: {p['panel']};
        color: {p['accent']};
        font-weight: bold;
    }}
    QSlider::groove:horizontal {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        height: 5px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {p['accent']};
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }}
    QSlider::groove:vertical {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        width: 5px;
        border-radius: 2px;
    }}
    QSlider::handle:vertical {{
        background: {p['accent']};
        height: 12px;
        margin: 0 -5px;
        border-radius: 6px;
    }}
    QCheckBox, QLabel {{ color: {p['text']}; }}
    QScrollBar:vertical {{
        background: {p['bg_alt']}; width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border']}; border-radius: 4px; min-height: 24px;
    }}
    """


def readable_dialog_qss(font_family: str = "", font_size: int = 11) -> str:
    """Always-dark, high-contrast styling for popup dialogs (Preferences,
    Sources, Radio, Shortcuts) so they stay legible regardless of the
    main app's light/dark theme choice."""
    family = font_family.strip() or "Segoe UI, Noto Sans, sans-serif"
    size = max(8, min(24, int(font_size or 11)))
    return f"""
    QDialog, QWidget {{
        background: #191c26;
        color: #eef0f8;
        font-family: {family};
        font-size: {size}px;
    }}
    QLabel {{ color: #eef0f8; }}
    QTabWidget::pane {{ border: 1px solid #333a4a; background: #20232e; }}
    QTabBar::tab {{
        background: #232633; color: #b9c1d9; padding: 7px 16px;
        border: 1px solid #333a4a; border-bottom: none;
    }}
    QTabBar::tab:selected {{ background: #20232e; color: #9fe0a0; font-weight: bold; }}
    QLineEdit, QComboBox, QSpinBox, QFontComboBox, QListWidget {{
        background: #10121a; color: #eef0f8; border: 1px solid #333a4a;
        border-radius: 3px; padding: 4px;
    }}
    QListWidget::item:selected {{ background: #2f6b2f; color: #ffffff; }}
    QCheckBox {{ color: #eef0f8; spacing: 8px; }}
    QPushButton {{
        background: #262a38; color: #eef0f8; border: 1px solid #3a3f4d;
        border-radius: 4px; padding: 5px 12px; font-weight: 600;
    }}
    QPushButton:hover {{ border: 1px solid #6fd36f; color: #9fe0a0; }}
    QPushButton:pressed {{ background: #2f6b2f; }}
    """


def transport_button_qss(theme_name: str) -> str:
    """Bigger, glossier styling for the transport buttons — same footprint,
    more Winamp-metal appeal (subtle gradient + inner highlight on press)."""
    p = palette(theme_name)
    return f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 {p['bg_alt']}, stop:0.5 {p['bg']}, stop:1 {p['bg_alt']});
        border: 1px solid {p['border']};
        border-radius: 5px;
        font-size: 13px;
        font-weight: bold;
        color: {p['text']};
    }}
    QPushButton:hover {{
        border: 1px solid {p['accent']};
        color: {p['accent']};
    }}
    QPushButton:pressed {{
        background: {p['accent_dim']};
    }}
    """


def seek_bar_qss(theme_name: str) -> str:
    """Bigger, high-contrast styling for the duration/seek bar, meant to sit
    on the dark LCD 'screen' panel — a bright, glowing accent fill on a
    near-black groove plus a large lit handle so playback position is easy
    to read and easy to grab at a glance, not just a thin generic slider."""
    p = palette(theme_name)
    return f"""
    QSlider::groove:horizontal {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        height: 10px;
        border-radius: 5px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                      stop:0 #d6ffe5, stop:0.5 {p['accent']}, stop:1 #238653);
        border: 1px solid {p['border']};
        border-radius: 5px;
    }}
    QSlider::add-page:horizontal {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        border-radius: 5px;
    }}
    QSlider::handle:horizontal {{
        background: qradialgradient(cx:0.5, cy:0.4, radius:0.6,
                      fx:0.5, fy:0.3, stop:0 #ffffff, stop:0.35 #c9ffda, stop:1 {p['accent']});
        width: 18px;
        height: 18px;
        margin: -5px 0;
        border-radius: 9px;
        border: 1px solid {p['border']};
    }}
    QSlider::handle:horizontal:hover {{
        background: qradialgradient(cx:0.5, cy:0.4, radius:0.6,
                     fx:0.5, fy:0.3, stop:0 #ffffff, stop:0.35 #d6ffe0, stop:1 #4fe374);
    }}
    """


def volume_slider_qss(theme_name: str) -> str:
    """A more readable, appealing volume slider: a visible colored fill for
    the current level (instead of a flat groove with no level indication),
    a bigger glowing handle, and enough height to actually see/grab."""
    p = palette(theme_name)
    return f"""
    QSlider::groove:horizontal {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                     stop:0 {p['accent_dim']}, stop:1 {p['accent']});
        border: 1px solid {p['border']};
        border-radius: 3px;
    }}
    QSlider::add-page:horizontal {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: qradialgradient(cx:0.5, cy:0.4, radius:0.6,
                     fx:0.5, fy:0.3, stop:0 #ffffff, stop:0.35 {p['accent']}, stop:1 {p['accent_dim']});
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
        border: 1px solid {p['border']};
    }}
    QSlider::handle:horizontal:hover {{
        border: 1px solid {p['accent']};
    }}
    """


def volume_value_label_qss(theme_name: str) -> str:
    """A small, theme-colored label for the live volume percentage that blends
    into the background (no panel box) so it reads cleanly alongside the
    skinned/unskinned volume slider."""
    p = palette(theme_name)
    return f"""
    QLabel {{
        color: {p['accent']};
        padding: 0 6px;
        font-size: 10px;
        font-weight: bold;
    }}
    """


def eq_toggle_qss(theme_name: str) -> str:
    """EQ toggle styling — glow green when engaged, matching classic Winamp."""
    p = palette(theme_name)
    return f"""
    QPushButton {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        border-radius: 4px;
        padding: 3px 10px;
        font-weight: bold;
        color: {p['text_dim']};
    }}
    QPushButton:checked {{
        background: {p['accent_dim']};
        border: 1px solid {p['accent']};
        color: {p['accent']};
    }}
    QPushButton:hover {{
        border: 1px solid {p['accent']};
    }}
    """


def eq_slider_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
    QSlider::groove:vertical {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        width: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:vertical {{
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.6,
                     fx:0.5, fy:0.4, stop:0 #ffffff, stop:0.3 {p['accent']}, stop:1 {p['accent_dim']});
        height: 14px;
        margin: 0 -5px;
        border-radius: 7px;
        border: 1px solid {p['border']};
    }}
    QSlider::sub-page:vertical {{
        background: {p['accent_dim']};
        border-radius: 3px;
    }}
    """
