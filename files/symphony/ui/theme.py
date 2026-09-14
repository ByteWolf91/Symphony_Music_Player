"""Theme definitions and QSS stylesheet generator for Symphony."""

DARK = {
    "name": "dark",
    "bg": "#12141a",
    "panel": "#1a1d26",
    "card": "#202430",
    "surface": "#232836",
    "border": "#2e3444",
    "accent": "#4a78e8",
    "accent_dim": "#3559b3",
    "accent_hover": "#5a88f8",
    "text": "#e8ecf4",
    "muted": "#7c859c",
    "highlight": "#2a3042",
    "selection": "#2f3854",
    "btn_border": "#3b4458",
    "btn_bevel_top": "#4a546c",
    "btn_bevel_bottom": "#161922",
    "btn_gradient_top": "#2a3040",
    "btn_gradient_bottom": "#1c202b",
    "btn_hover_top": "#363d50",
    "btn_hover_bottom": "#242938",
    "btn_pressed_top": "#141720",
    "btn_pressed_bottom": "#1f2430",
    "toggle_bg": "#1d212c",
    "toggle_border": "#363e52",
    "toggle_on_bg": "#233357",
    "toggle_on_border": "#4a78e8",
    "toggle_on_text": "#7aa5ff",
}

LIGHT = {
    "name": "light",
    "bg": "#eef1f6",
    "panel": "#f7f9fc",
    "card": "#ffffff",
    "surface": "#f0f3f8",
    "border": "#d2d8e4",
    "accent": "#2b5cd9",
    "accent_dim": "#4873e3",
    "accent_hover": "#1d47b8",
    "text": "#1a202c",
    "muted": "#5f6c84",
    "highlight": "#e2e7f1",
    "selection": "#dbe4f9",
    "btn_border": "#b8c2d4",
    "btn_bevel_top": "#ffffff",
    "btn_bevel_bottom": "#9aa6bd",
    "btn_gradient_top": "#fcfdfe",
    "btn_gradient_bottom": "#e4e9f2",
    "btn_hover_top": "#ffffff",
    "btn_hover_bottom": "#edf2fa",
    "btn_pressed_top": "#d4dceb",
    "btn_pressed_bottom": "#e8edf6",
    "toggle_bg": "#e8edf5",
    "toggle_border": "#bec9dc",
    "toggle_on_bg": "#dce6fc",
    "toggle_on_border": "#2b5cd9",
    "toggle_on_text": "#1b44b8",
}

THEMES = {"dark": DARK, "light": LIGHT}

def palette(theme_name: str) -> dict:
    return THEMES.get(theme_name, DARK)

def transport_button_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QWidget#transport_wrap QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['btn_gradient_top']}, stop:1 {p['btn_gradient_bottom']});
    color: {p['text']};
    border: 1px solid {p['btn_border']};
    border-top: 1px solid {p['btn_bevel_top']};
    border-bottom: 2px solid {p['btn_bevel_bottom']};
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    padding: 4px 10px;
    margin: 1px 2px;
}}
QWidget#transport_wrap QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['btn_hover_top']}, stop:1 {p['btn_hover_bottom']});
    border: 1px solid {p['accent']};
    border-top: 1px solid {p['accent_hover']};
    color: #ffffff;
}}
QWidget#transport_wrap QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['btn_pressed_top']}, stop:1 {p['btn_pressed_bottom']});
    border: 1px solid {p['btn_bevel_bottom']};
    border-top: 2px solid {p['btn_bevel_bottom']};
    padding-top: 5px;
    padding-bottom: 3px;
}}
"""

def readable_dialog_qss(font_family: str = "", font_size: int = 11) -> str:
    family_decl = f"font-family: '{font_family}';" if font_family else ""
    return f"""
QDialog, QMessageBox, QMenu {{
    {family_decl}
    font-size: {font_size}px;
}}
"""

def seek_bar_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QSlider::groove:horizontal {{
    height: 6px;
    background: {p['border']};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {p['accent']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {p['text']};
    border: 1px solid {p['accent']};
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}}
"""

def volume_slider_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QSlider::groove:horizontal {{
    height: 4px;
    background: {p['border']};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {p['accent']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p['text']};
    border: 1px solid {p['border']};
    width: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
"""

def volume_value_label_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QLabel {{
    color: {p['muted']};
    font-size: 10px;
    font-weight: bold;
    min-width: 28px;
}}
"""

def eq_toggle_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QPushButton {{
    background: {p['toggle_bg']};
    color: {p['muted']};
    border: 1px solid {p['toggle_border']};
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
    padding: 3px 8px;
}}
QPushButton:hover {{
    background: {p['card']};
    border-color: {p['accent']};
    color: {p['text']};
}}
QPushButton:checked {{
    background: {p['toggle_on_bg']};
    border-color: {p['toggle_on_border']};
    color: {p['toggle_on_text']};
}}
"""

def eq_slider_qss(theme_name: str) -> str:
    p = palette(theme_name)
    return f"""
QSlider::groove:vertical {{
    width: 4px;
    background: {p['border']};
    border-radius: 2px;
}}
QSlider::sub-page:vertical {{
    background: {p['border']};
    border-radius: 2px;
}}
QSlider::add-page:vertical {{
    background: {p['accent']};
    border-radius: 2px;
}}
QSlider::handle:vertical {{
    background: {p['text']};
    border: 1px solid {p['border']};
    height: 12px;
    margin: 0 -4px;
    border-radius: 6px;
}}
"""

def app_stylesheet(theme_name: str = "dark", font_family: str = "", font_size: int = 11) -> str:
    p = palette(theme_name)
    family_decl = f"font-family: '{font_family}';" if font_family else ""
    return f"""
* {{
    {family_decl}
    font-size: {font_size}px;
}}
QMainWindow, QDialog {{
    background-color: {p['bg']};
    color: {p['text']};
}}
QWidget#central_widget {{
    background-color: {p['bg']};
}}
QSplitter::handle {{
    background: {p['border']};
}}
QLabel {{
    color: {p['text']};
}}
QPushButton {{
    background: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 3px;
    padding: 4px 8px;
}}
QPushButton:hover {{
    background: {p['highlight']};
    border-color: {p['accent']};
}}
QPushButton:pressed {{
    background: {p['card']};
}}
QPushButton#toggle_button,
QPushButton[checkable="true"] {{
    background: {p['toggle_bg']};
    color: {p['muted']};
    border: 1px solid {p['toggle_border']};
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
    min-height: 22px;
    max-height: 25px;
    padding: 2px 6px;
}}
QPushButton#toggle_button:hover,
QPushButton[checkable="true"]:hover {{
    background: {p['card']};
    border-color: {p['accent']};
    color: {p['text']};
}}
QPushButton#toggle_button:checked,
QPushButton[checkable="true"]:checked {{
    background: {p['toggle_on_bg']};
    border-color: {p['toggle_on_border']};
    color: {p['toggle_on_text']};
}}
QListWidget, QTableView, QTreeView {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 3px;
    outline: none;
}}
QListWidget::item:selected, QTableView::item:selected {{
    background-color: {p['selection']};
    color: {p['text']};
}}
QScrollBar:vertical {{
    background: {p['bg']};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['border']};
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QMenu {{
    background-color: {p['panel']};
    color: {p['text']};
    border: 1px solid {p['border']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background-color: {p['accent']};
    color: #ffffff;
}}
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 3px;
    padding: 3px 6px;
    selection-background-color: {p['selection']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {p['accent']};
}}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    color: {p['muted']};
    background-color: {p['panel']};
}}
QComboBox {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 3px;
    padding: 3px 6px;
}}
QComboBox:hover {{
    border-color: {p['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    selection-background-color: {p['selection']};
    selection-color: {p['text']};
    outline: none;
}}
QProgressBar {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 3px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {p['accent']};
    border-radius: 3px;
}}
QTabWidget::pane {{
    background-color: {p['bg']};
    border: 1px solid {p['border']};
    border-radius: 3px;
}}
QTabBar {{
    background-color: transparent;
}}
QTabBar::tab {{
    background: {p['panel']};
    color: {p['muted']};
    border: 1px solid {p['border']};
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    padding: 6px 12px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {p['card']};
    color: {p['text']};
    border-color: {p['accent']};
}}
QTabBar::tab:hover:!selected {{
    background: {p['highlight']};
    color: {p['text']};
}}
QCheckBox {{
    color: {p['text']};
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    background-color: {p['card']};
    border: 1px solid {p['border']};
    border-radius: 2px;
}}
QCheckBox::indicator:checked {{
    background-color: {p['accent']};
    border-color: {p['accent']};
}}
"""
