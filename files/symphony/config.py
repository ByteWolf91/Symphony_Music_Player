"""Simple local JSON config store — lives at ~/.symphony/config.json."""
import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".symphony")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "volume": 80,
    "balance": 0,
    "shuffle": False,
    "repeat": False,
    "last_skin_path": "",
    "remember_volume": True,
    "autoplay_import": True,
    "scan_subfolders": True,
    "confirm_clear": True,
    "confirm_quit": False,
    "restore_skin": True,
    "ui_scale": 100,
    "theme": "dark",
    "read_tags": True,
    "always_on_top": False,
    "show_artist_genre": True,
    "radio_favorites": [],
    "now_playing_height": 70,
    "ui_font_family": "",
    "ui_font_size": 11,
    "list_font_family": "",       # playlist / library font ("" = same as UI)
    "list_font_size": 0,          # 0 = same as UI size
    "display_font_family": "",    # now-playing display font ("" = Courier New)
    "display_font_size": 11,
    "custom_font_files": [],      # .ttf/.otf files the user added
    "restore_playlist": True,
    "session_playlist": [],
    "window_width": 380,
    "window_height": 300,
    "eq_enabled": False,
    "eq_preset": "Flat",
    "eq_preamp": 0.0,
    "eq_bands": [0.0] * 10,
    "remember_playlists": True,
    "recent_playlists": [],
}


def load():
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save(config: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
