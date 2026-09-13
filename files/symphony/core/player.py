"""Playback engine built on LibVLC (via python-vlc).

Using LibVLC instead of a narrow codec library is what gives Symphony broad
format support "for free" — LibVLC's own demuxers/decoders handle MP3, FLAC,
WAV, OGG/Opus, WMA, AAC/M4A, APE, AIFF, and quite a bit more, and it can also
play direct stream URLs (used by the internet radio feature) without any
extra plumbing.
"""
import vlc

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# Discrete channel modes LibVLC exposes (there's no continuous stereo-balance
# API in libvlc's public surface, so "balance" is approximated as a small set
# of discrete positions rather than a truly continuous pan).
BALANCE_STEREO = 1
BALANCE_LEFT_ONLY = 3
BALANCE_RIGHT_ONLY = 4


class PlayerEngine(QObject):
    position_changed = pyqtSignal(float, float)  # current_seconds, duration_seconds
    state_changed = pyqtSignal(str)               # "playing" | "paused" | "stopped" | "ended"
    track_ended = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._instance = vlc.Instance("--no-video")
        self._player = self._instance.media_player_new()

        # Keep the EQ values in Python and apply them as one operation.  Some
        # LibVLC builds detach the equalizer when a new media object is loaded;
        # re-applying the same object in load() makes the UI reliable across
        # those builds instead of leaving the sliders looking active while the
        # audio stays flat.
        self._equalizer = vlc.AudioEqualizer()
        # Band count/frequency are properties of libvlc's equalizer system as a
        # whole, not of a specific AudioEqualizer instance, so python-vlc
        # exposes them as module-level libvlc_* functions rather than methods
        # on the AudioEqualizer object.
        self.band_count = int(vlc.libvlc_audio_equalizer_get_band_count())
        self.band_frequencies = [
            float(vlc.libvlc_audio_equalizer_get_band_frequency(i))
            for i in range(self.band_count)
        ]
        self._classic_frequencies = (
            60.0, 170.0, 310.0, 600.0, 1000.0,
            3000.0, 6000.0, 12000.0, 14000.0, 16000.0,
        )
        self._classic_band_map = self._build_classic_band_map()
        self._eq_enabled = False
        self._eq_preamp = 0.0
        self._eq_bands = [0.0] * len(self._classic_frequencies)

        self._volume = 80
        self._balance = 0  # -100..100, UI-facing value even though playback is discrete
        self._muted = False

        events = self._player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

        self._poll_timer = QTimer()
        self._poll_timer.setInterval(250)
        self._poll_timer.timeout.connect(self._poll_position)
        self._poll_timer.start()

    # ---------- loading / transport ----------
    def load(self, path_or_url: str):
        media = self._instance.media_new(path_or_url)
        self._player.set_media(media)
        self._apply_equalizer()

    def play(self):
        self._player.play()
        self.state_changed.emit("playing")

    def pause(self):
        self._player.set_pause(1)
        self.state_changed.emit("paused")

    def stop(self):
        self._player.stop()
        self.state_changed.emit("stopped")

    def is_playing(self) -> bool:
        return self._player.is_playing() == 1

    # ---------- seeking ----------
    def get_time_seconds(self) -> float:
        t = self._player.get_time()
        return max(0.0, t / 1000.0) if t is not None and t >= 0 else 0.0

    def get_length_seconds(self) -> float:
        length = self._player.get_length()
        return max(0.0, length / 1000.0) if length and length > 0 else 0.0

    def seek_seconds(self, seconds: float):
        self._player.set_time(int(max(0, seconds) * 1000))

    def seek_relative(self, delta_seconds: float):
        self.seek_seconds(self.get_time_seconds() + delta_seconds)

    # ---------- volume / balance ----------
    def set_volume(self, vol_0_100: int):
        self._volume = max(0, min(100, vol_0_100))
        self._player.audio_set_volume(self._volume)

    def get_volume(self) -> int:
        return self._volume

    def set_balance(self, bal_neg100_100: int):
        """Approximate balance using LibVLC's discrete channel-routing modes."""
        self._balance = max(-100, min(100, bal_neg100_100))
        if self._balance <= -60:
            self._player.audio_set_channel(BALANCE_LEFT_ONLY)
        elif self._balance >= 60:
            self._player.audio_set_channel(BALANCE_RIGHT_ONLY)
        else:
            self._player.audio_set_channel(BALANCE_STEREO)

    def get_balance(self) -> int:
        return self._balance

    # ---------- equalizer ----------
    def set_preamp(self, db: float):
        self._eq_preamp = max(-20.0, min(20.0, float(db)))
        self._equalizer.set_preamp(self._eq_preamp)
        self._apply_equalizer()

    def set_band(self, index: int, db: float):
        """Set a LibVLC band by its actual index."""
        if 0 <= index < self.band_count:
            self._equalizer.set_amp_at_index(float(db), index)
            self._apply_equalizer()

    def set_classic_band(self, index: int, db: float):
        """Set one of the ten Winamp bands, mapped to this LibVLC build."""
        if 0 <= index < len(self._eq_bands):
            self._eq_bands[index] = max(-20.0, min(20.0, float(db)))
            actual_index = self._classic_band_map[index]
            self.set_band(actual_index, self._eq_bands[index])

    def get_classic_band_values(self):
        return list(self._eq_bands)

    def get_preamp(self):
        return self._eq_preamp

    def set_eq_enabled(self, enabled: bool):
        self._eq_enabled = bool(enabled)
        self._apply_equalizer()

    def apply_preset_db(self, values_10_band, preamp_db=0.0):
        """Apply classic Winamp values to the nearest LibVLC frequencies."""
        self.set_preamp(preamp_db)
        for i, value in enumerate(values_10_band[:len(self._eq_bands)]):
            self._eq_bands[i] = max(-20.0, min(20.0, float(value)))
            self._equalizer.set_amp_at_index(
                self._eq_bands[i], self._classic_band_map[i])
        self._apply_equalizer()

    def _build_classic_band_map(self):
        if not self.band_frequencies:
            return [min(i, max(0, self.band_count - 1))
                    for i in range(len(self._classic_frequencies))]
        return [
            min(
                range(len(self.band_frequencies)),
                key=lambda actual: abs(
                    self.band_frequencies[actual] - classic
                ),
            )
            for classic in self._classic_frequencies
        ]

    def _apply_equalizer(self):
        # Passing None to set_equalizer disables it entirely.  Reusing one
        # equalizer object is important: creating a new object per slider tick
        # makes some python-vlc versions silently ignore later changes.
        self._player.set_equalizer(self._equalizer if self._eq_enabled else None)

    # ---------- internal ----------
    def _poll_position(self):
        self.position_changed.emit(self.get_time_seconds(), self.get_length_seconds())

    def _on_end_reached(self, event):
        self.track_ended.emit()
