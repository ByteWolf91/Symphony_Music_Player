"""Playlist model. A track is a small dict-like record so it can hold either
a local file path or a resolved stream URL (internet radio), uniformly."""
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    title: str
    source: str            # "local" | "radio" | "cd"
    uri: str                # local file path or playable stream URL
    duration: Optional[float] = None
    artist: str = ""
    genre: str = ""
    bitrate: Optional[int] = None       # bits per second
    sample_rate: Optional[int] = None   # Hz
    album: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title, "source": self.source, "uri": self.uri,
            "duration": self.duration, "artist": self.artist, "genre": self.genre,
            "bitrate": self.bitrate, "sample_rate": self.sample_rate,
            "album": self.album,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Track":
        return cls(
            title=d.get("title", ""), source=d.get("source", "local"),
            uri=d.get("uri", ""), duration=d.get("duration"),
            artist=d.get("artist", ""), genre=d.get("genre", ""),
            bitrate=d.get("bitrate"), sample_rate=d.get("sample_rate"),
            album=d.get("album", ""),
        )


class Playlist:
    def __init__(self):
        self.tracks: list[Track] = []
        self.current_index: int = -1
        self.shuffle: bool = False
        self.repeat: bool = False
        self._shuffle_bag: list[int] = []

    def add(self, track: Track):
        self.tracks.append(track)

    def remove(self, index: int):
        if 0 <= index < len(self.tracks):
            del self.tracks[index]
            if index == self.current_index:
                self.current_index = -1
            elif index < self.current_index:
                self.current_index -= 1

    def clear(self):
        self.tracks.clear()
        self.current_index = -1

    def sort_by_title(self):
        current = self.current() if self.current_index >= 0 else None
        self.tracks.sort(key=lambda t: t.title.lower())
        if current is not None:
            self.current_index = self.tracks.index(current)

    def current(self) -> Optional[Track]:
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None

    def next_index(self) -> Optional[int]:
        if not self.tracks:
            return None
        if self.shuffle:
            return random.randrange(len(self.tracks))
        return (self.current_index + 1) % len(self.tracks)

    def prev_index(self) -> Optional[int]:
        if not self.tracks:
            return None
        if self.shuffle:
            return random.randrange(len(self.tracks))
        return (self.current_index - 1) % len(self.tracks)

    def total_duration(self) -> float:
        return sum(t.duration or 0 for t in self.tracks)
