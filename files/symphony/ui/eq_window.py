from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                              QPushButton, QComboBox)

from symphony.ui import theme as theme_mod

PRESETS = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [5, 4, 2, 0, -2, -2, 0, 2, 4, 5],
    "Pop": [-1, 2, 4, 4, 2, 0, -1, -1, -1, -1],
    "Jazz": [3, 2, 0, 1, -1, -1, 0, 2, 3, 4],
    "Classical": [4, 3, 2, 0, 0, 0, -2, -2, -2, 3],
    "Bass Boost": [8, 7, 6, 3, 0, 0, 0, 0, 0, 0],
    "Treble Boost": [0, 0, 0, 0, 0, 2, 4, 6, 7, 8],
}
BAND_LABELS = ["60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]


class EqWindow(QWidget):
    # Emitted whenever the window is actually shown/hidden (including via its
    # own titlebar close button), so the main window's EQ toggle button can
    # stay in sync instead of needing a second click to react.
    visibility_changed = pyqtSignal(bool)

    def __init__(
        self, player_engine, skin_provider, theme_name="dark",
        font_family="", font_size=11, parent=None
    ):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Symphony Equalizer")
        self.player = player_engine
        self._skin_provider = skin_provider
        self._theme = theme_name
        self._font_family = font_family
        self._font_size = font_size
        self.setMinimumSize(420, 180)
        self.resize(520, 220)
        self._apply_window_style()
        self._drag_pos = None
        self._build_ui()

    def set_theme(self, theme_name):
        self._theme = theme_name
        self._apply_window_style()
        self.on_btn.setStyleSheet(theme_mod.eq_toggle_qss(theme_name))
        for group in [self.preamp_slider] + self.band_sliders:
            group["slider"].setStyleSheet(theme_mod.eq_slider_qss(theme_name))

    def set_font(self, font_family="", font_size=11):
        self._font_family = font_family
        self._font_size = font_size
        self._apply_window_style()

    def _apply_window_style(self):
        palette = theme_mod.palette(self._theme)
        family = self._font_family.strip() or "Segoe UI, Noto Sans, sans-serif"
        size = max(8, min(24, int(self._font_size or 11)))
        self.setStyleSheet(
            f"QWidget {{ background:{palette['bg']}; border:1px solid #15171d; "
            f"font-family:{family}; font-size:{size}px; }}"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titlebar = QWidget()
        titlebar.setFixedHeight(16)
        titlebar.setStyleSheet("background:#152048;")
        tb_layout = QHBoxLayout(titlebar)
        tb_layout.setContentsMargins(4, 0, 4, 0)
        label = QLabel("EQUALIZER")
        label.setStyleSheet("color:#cfe0ff; font-weight:bold;")
        close_btn = QPushButton("×")
        close_btn.setFixedSize(14, 14)
        close_btn.clicked.connect(self.hide)
        tb_layout.addWidget(label)
        tb_layout.addStretch()
        tb_layout.addWidget(close_btn)
        titlebar.mousePressEvent = self._start_drag
        titlebar.mouseMoveEvent = self._do_drag
        root.addWidget(titlebar)

        top = QHBoxLayout()
        self.on_btn = QPushButton("OFF")
        self.on_btn.setCheckable(True)
        self.on_btn.setStyleSheet(theme_mod.eq_toggle_qss(self._theme))
        self.on_btn.toggled.connect(self._on_toggled)
        reset_btn = QPushButton("RESET")
        reset_btn.setToolTip("Return all bands and preamp to 0dB")
        reset_btn.clicked.connect(self._reset)
        self.preset_box = QComboBox()
        self.preset_box.addItems(PRESETS.keys())
        self.preset_box.currentTextChanged.connect(self._apply_preset)
        top.addWidget(self.on_btn)
        top.addWidget(reset_btn)
        top.addWidget(self.preset_box, 1)
        root.addLayout(top)

        sliders_row = QHBoxLayout()
        self.preamp_slider = self._make_slider("PRE")
        sliders_row.addLayout(self.preamp_slider["layout"])
        self.band_sliders = []
        for label_text in BAND_LABELS:
            group = self._make_slider(label_text)
            sliders_row.addLayout(group["layout"])
            self.band_sliders.append(group)
        root.addLayout(sliders_row)

        self.preamp_slider["slider"].valueChanged.connect(
            lambda v: self.player.set_preamp(float(v)))
        for i, group in enumerate(self.band_sliders):
            group["slider"].valueChanged.connect(
                lambda v, idx=i: self.player.set_classic_band(idx, float(v)))

    def _make_slider(self, label_text):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        value_label = QLabel("0dB")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color:#7fd3ff; font-weight:bold;")
        slider = QSlider(Qt.Vertical)
        slider.setRange(-12, 12)
        slider.setValue(0)
        slider.setFixedHeight(100)
        slider.setTickInterval(6)
        slider.setStyleSheet(theme_mod.eq_slider_qss(self._theme))
        slider.valueChanged.connect(
            lambda v, lab=value_label: lab.setText(f"{v:+d}dB" if v else "0dB"))
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color:#9ab; font-weight:bold;")
        layout.addWidget(value_label)
        layout.addWidget(slider, alignment=Qt.AlignHCenter)
        layout.addWidget(label)
        return {"layout": layout, "slider": slider}

    def _on_toggled(self, checked):
        self.player.set_eq_enabled(checked)
        self.on_btn.setText("ON" if checked else "OFF")

    def _apply_preset(self, name):
        values = PRESETS.get(name, PRESETS["Flat"])
        for group, val in zip(self.band_sliders, values):
            group["slider"].setValue(val)
        # Choosing a preset is an explicit request to hear the EQ. The ON
        # switch still lets users bypass it without losing their settings.
        self.on_btn.setChecked(True)

    def _reset(self):
        self.preset_box.setCurrentText("Flat")
        self._apply_preset("Flat")

    def load_values(self, enabled=False, preamp=0.0, bands=None, preset="Flat"):
        """Restore EQ state after all controls exist."""
        self.preset_box.blockSignals(True)
        if preset in PRESETS:
            self.preset_box.setCurrentText(preset)
        self.preset_box.blockSignals(False)
        self.preamp_slider["slider"].setValue(int(preamp))
        for group, value in zip(self.band_sliders, bands or [0] * 10):
            group["slider"].setValue(int(value))
        self.on_btn.setChecked(bool(enabled))
        self.player.set_eq_enabled(bool(enabled))

    def snapshot(self):
        return {
            "enabled": self.on_btn.isChecked(),
            "preamp": self.preamp_slider["slider"].value(),
            "bands": [group["slider"].value() for group in self.band_sliders],
            "preset": self.preset_box.currentText(),
        }

    def _start_drag(self, event):
        self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _do_drag(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
