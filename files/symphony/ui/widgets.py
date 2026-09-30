"""Small reusable widgets shared by the player windows."""
import random

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFont
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QSlider, QStyle,
                             QStyleOptionSlider)


class WheelSlider(QSlider):
    """A QSlider that reports mouse-wheel scrolling through a dedicated
    signal instead of Qt's default behavior of quietly nudging its own
    value by one step. That default is wrong for a couple of our sliders:
    the seek bar's value is driven by playback position, not by the user,
    so a caller needs to turn a scroll into a player seek instead of a raw
    value change. Keeping this generic (just emit +1/-1 per notch and let
    the owner decide what to do with it) lets both the volume slider and
    the seek bar share the same class."""

    wheel_scrolled = pyqtSignal(int)  # +1 per notch up/forward, -1 down/back

    def __init__(self, *args, jump_on_click=False, **kwargs):
        super().__init__(*args, **kwargs)
        # When True, a left click anywhere on the bar jumps the handle to that
        # spot (and dragging keeps following the mouse). sliderPressed /
        # sliderReleased fire exactly as they do for a normal handle drag, so
        # the owner can seek on release. The mouse wheel is unaffected.
        self._jump_on_click = jump_on_click

    def _value_at(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = self.style()
        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        handle = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        span = max(1, groove.width() - handle.width())
        x = pos.x() - groove.x() - handle.width() // 2
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), x, span, opt.upsideDown)

    def mousePressEvent(self, event):
        if self._jump_on_click and event.button() == Qt.LeftButton:
            self.setSliderDown(True)
            self.setValue(self._value_at(event.pos()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._jump_on_click and self.isSliderDown():
            self.setValue(self._value_at(event.pos()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._jump_on_click and event.button() == Qt.LeftButton and self.isSliderDown():
            self.setValue(self._value_at(event.pos()))
            self.setSliderDown(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        steps = delta // 120 if abs(delta) >= 120 else (1 if delta > 0 else -1)
        self.wheel_scrolled.emit(steps)
        event.accept()


class LCDDigits(QWidget):
    """Renders a time string (MM:SS) either from real skin digit sprites
    (numbers.bmp) if a skin is loaded, or a monospace fallback font."""

    def __init__(self, skin_provider, parent=None):
        super().__init__(parent)
        self._skin_provider = skin_provider  # callable -> WszSkin | None
        self._text = "00:00"
        self.setFixedHeight(13)

    def set_text(self, text: str):
        if text != self._text:
            self._text = text
            self.update()

    def sizeHint(self):
        return self.fixedSize() if self.hasHeightForWidth() else super().sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        skin = self._skin_provider()
        x = 0
        if skin and skin.loaded and "numbers.bmp" in skin.images:
            for ch in self._text:
                px = skin.digit(ch if ch.isdigit() else " ")
                if px:
                    painter.drawPixmap(x, 0, px)
                    x += px.width()
                else:
                    x += 9
            self.setFixedWidth(max(x, 1))
        else:
            painter.setPen(QColor("#7fff3f"))
            font = QFont("Courier New", 12, QFont.Bold)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self._text)
        painter.end()


class Visualizer(QWidget):
    """Classic Winamp-style bar spectrum analyzer.

    Note: this is an animated approximation driven by playback state, not a
    real-time FFT of the decoded audio. Getting genuine per-band amplitude
    out of LibVLC requires tapping raw PCM via its audio callback API
    (libvlc_audio_set_callbacks) — doable, but with no display/audio device
    available to test against in the environment this was written in, a
    verified-correct raw-callback implementation was too risky to ship
    untested. This gives the right look and reacts to play/pause/stop;
    swapping in a real analyser later just means feeding real bar heights
    into `self.levels` instead of the random walk below.
    """

    BAR_COUNT = 19

    def __init__(self, skin_provider, parent=None):
        super().__init__(parent)
        self._skin_provider = skin_provider
        self.levels = [0.0] * self.BAR_COUNT
        self._playing = False
        self.setFixedSize(76, 16)
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_playing(self, playing: bool):
        self._playing = playing

    def _tick(self):
        for i in range(self.BAR_COUNT):
            target = random.uniform(0.15, 1.0) if self._playing else 0.0
            self.levels[i] += (target - self.levels[i]) * 0.5
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#14161f"))
        skin = self._skin_provider()
        palette = skin.visualizer_palette() if (skin and skin.loaded) else None

        bar_w = 3
        gap = 1
        for i, level in enumerate(self.levels):
            h = max(1, round(level * 16))
            x = i * (bar_w + gap)
            if x + bar_w > self.width():
                break
            if palette:
                idx = min(len(palette) - 1, round(level * (len(palette) - 1)))
                r, g, b = palette[idx]
                color = QColor(r, g, b)
                painter.fillRect(x, 16 - h, bar_w, h, color)
            else:
                grad = QLinearGradient(0, 16 - h, 0, 16)
                grad.setColorAt(0.0, QColor("#818cf8"))
                grad.setColorAt(0.6, QColor("#6366f1"))
                grad.setColorAt(1.0, QColor("#4f46e5"))
                painter.fillRect(x, 16 - h, bar_w, h, grad)
        painter.end()


class TitleScroller(QLabel):
    """Horizontally scrolling now-playing text, Winamp LCD style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full_text = ""
        self._offset = 0
        self.set_display_font("", 11)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def set_display_font(self, family: str = "", size: int = 11):
        fam = (family or "").strip().replace("'", "")
        stack = f"'{fam}', 'Courier New', monospace" if fam else "'Courier New', monospace"
        self.setStyleSheet(
            f"color:#7fff3f; font-family:{stack}; font-size:{int(size or 11)}px;")

    def set_text(self, text: str):
        self._full_text = text + "   //   "
        self._offset = 0

    def _advance(self):
        if not self._full_text:
            return
        self._offset = (self._offset + 1) % len(self._full_text)
        rotated = self._full_text[self._offset:] + self._full_text[:self._offset]
        self.setText(rotated[:40])
