"""Classic Winamp 2.x (.wsz) skin loader.

A .wsz file is just a zip archive of BMPs plus a couple of text config files.
This is a best-effort renderer: it covers the pieces with the biggest visual
impact (main background, titlebar, transport buttons, shuffle/repeat/EQ/
playlist toggle buttons, LCD digit font, EQ window background, playlist
colors, visualizer colors) using the widely-documented classic sprite-sheet
layout. It does not attempt full spec fidelity (window-shade mode, every
posbar/volume/balance sub-frame, gen.bmp windows, cursors) — for that level
of completeness see the open-source Webamp project, which is dedicated
entirely to pixel-perfect classic skin rendering.

All coordinates below reflect the standard classic-skin sprite-sheet layout
(cbuttons.bmp 136x36 = 6 buttons x 2 states x 18px tall; numbers.bmp 99x13 =
11 glyphs x 9px wide; etc.) as documented across the Winamp skinning
community. Non-standard/custom-sized skins may not slice perfectly — code
degrades gracefully (falls back to the built-in look) if a file is missing
or a crop goes out of bounds.
"""
import io
import os
import zipfile
from typing import Optional

from PIL import Image
from PyQt5.QtGui import QPixmap, QImage

# Symphony ships with the "base-2.91" classic Winamp skin bundled at
# symphony/skins/base-2.91.wsz, and uses it as the out-of-the-box default
# look (see MainWindow._resolve_startup_skin) instead of the plain built-in
# fallback rendering. Users can still switch to any other .wsz at any time
# via Options -> Load Skin.
DEFAULT_SKIN_NAME = "base-2.91.wsz"


def default_skin_path() -> str:
    """Absolute path to the bundled default skin, regardless of install
    location (site-packages, a Linux distro's /usr/share/symphony, or a
    plain checkout)."""
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(package_root, "skins", DEFAULT_SKIN_NAME)


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())


class WszSkin:
    def __init__(self):
        self.name = "Default"
        self.images: dict[str, Image.Image] = {}
        self.pledit_colors: dict[str, str] = {}
        self.viscolors: list[tuple[int, int, int]] = []
        self.loaded = False

    @classmethod
    def load(cls, path: str) -> "WszSkin":
        skin = cls()
        skin.name = path.split("/")[-1].split("\\")[-1]
        try:
            with zipfile.ZipFile(path, "r") as zf:
                lookup = {info.filename.lower().split("/")[-1]: info for info in zf.infolist()}

                def read_bmp(fname):
                    info = lookup.get(fname)
                    if not info:
                        return None
                    try:
                        with zf.open(info) as f:
                            return Image.open(io.BytesIO(f.read())).convert("RGBA")
                    except Exception:
                        return None

                for bmp_name in (
                    "main.bmp", "titlebar.bmp", "cbuttons.bmp", "shufrep.bmp",
                    "numbers.bmp", "text.bmp", "eqmain.bmp", "playpaus.bmp",
                    "posbar.bmp", "volume.bmp", "balance.bmp", "monoster.bmp",
                    "pledit.bmp",
                ):
                    img = read_bmp(bmp_name)
                    if img is not None:
                        skin.images[bmp_name] = img

                pledit_info = lookup.get("pledit.txt")
                if pledit_info:
                    with zf.open(pledit_info) as f:
                        skin.pledit_colors = _parse_ini_colors(f.read().decode("latin-1"))

                viscolor_info = lookup.get("viscolor.txt")
                if viscolor_info:
                    with zf.open(viscolor_info) as f:
                        skin.viscolors = _parse_viscolors(f.read().decode("latin-1"))

            skin.loaded = "main.bmp" in skin.images
        except (zipfile.BadZipFile, OSError):
            skin.loaded = False
        return skin

    # ---- crop helpers, return QPixmap or None ----
    def crop(self, bmp_name: str, box: tuple) -> Optional[QPixmap]:
        img = self.images.get(bmp_name)
        if img is None:
            return None
        try:
            l, t, r, b = box
            if r > img.width or b > img.height or l < 0 or t < 0:
                return None
            return _pil_to_qpixmap(img.crop(box))
        except Exception:
            return None

    def main_background(self) -> Optional[QPixmap]:
        img = self.images.get("main.bmp")
        return _pil_to_qpixmap(img.crop((0, 0, 275, 116))) if img else None

    def eq_background(self) -> Optional[QPixmap]:
        img = self.images.get("eqmain.bmp")
        return _pil_to_qpixmap(img.crop((0, 0, 275, 116))) if img else None

    def titlebar(self, focused=True) -> Optional[QPixmap]:
        y = 0 if focused else 15
        return self.crop("titlebar.bmp", (27, y, 27 + 275, y + 14))

    # cbuttons.bmp: 6 columns (prev, play, pause, stop, next, eject) x 2 rows
    # (normal / pressed). Prev/play/pause/stop/next are 23px wide, eject ~22px.
    CBUTTON_ORDER = ["previous", "play", "pause", "stop", "next"]

    def transport_button(self, name: str, pressed=False) -> Optional[QPixmap]:
        y = 18 if pressed else 0
        if name == "eject":
            x = 5 * 23
            return self.crop("cbuttons.bmp", (x, y, x + 22, y + 18))
        idx = self.CBUTTON_ORDER.index(name)
        x = idx * 23
        return self.crop("cbuttons.bmp", (x, y, x + 23, y + 18))

    # shufrep.bmp: shuffle/repeat/EQ/playlist toggle buttons.
    # Row layout (each row 15px early Winamp2 skins use 43x36 blocks, but the
    # de-facto standard grid used by most tools is: shuffle @ (28,0..3),
    # repeat @ (0,0..3) each state stacked; EQ/PL toggle buttons live at the
    # bottom of the same sheet. We slice defensively and fall back silently.
    def toggle_button(self, name: str, on: bool, pressed: bool) -> Optional[QPixmap]:
        rows = {
            ("repeat", False, False): 0, ("repeat", False, True): 1,
            ("repeat", True, False): 2, ("repeat", True, True): 3,
        }
        if name in ("shuffle", "repeat"):
            row = rows.get(("repeat", on, pressed), 0)
            x = 28 if name == "shuffle" else 0
            y = row * 15
            return self.crop("shufrep.bmp", (x, y, x + 28, y + 15))
        if name in ("eq", "playlist"):
            base_y = 72 if not on else 89
            x = 0 if name == "eq" else 23
            y = base_y + (0 if not pressed else 0)
            return self.crop("shufrep.bmp", (x, y, x + 23, y + 12))
        return None

    # numbers.bmp: 11 glyphs (0-9, blank) each 9x13
    def digit(self, ch: str) -> Optional[QPixmap]:
        glyph_order = "0123456789 "
        idx = glyph_order.index(ch) if ch in glyph_order else 10
        x = idx * 9
        return self.crop("numbers.bmp", (x, 0, x + 9, 13))

    def visualizer_palette(self):
        """Returns list of (r,g,b) tuples from viscolor.txt if present,
        else a reasonable default green/yellow/red gradient."""
        if self.viscolors:
            return self.viscolors
        return [(0, 255, 0)] * 16 + [(255, 255, 0)] * 5 + [(255, 0, 0)] * 3


def _parse_ini_colors(text: str) -> dict:
    colors = {}
    for line in text.splitlines():
        if "=" in line:
            key, _, val = line.partition("=")
            colors[key.strip().lower()] = val.strip()
    return colors


def _parse_viscolors(text: str):
    out = []
    for line in text.splitlines():
        line = line.split(",")
        nums = [p.strip() for p in line if p.strip().lstrip("-").isdigit()]
        if len(nums) >= 3:
            r, g, b = (int(nums[0]), int(nums[1]), int(nums[2]))
            out.append((r, g, b))
    return out
