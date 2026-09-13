"""Best-effort audio tag reading (artist / title / genre / duration).

Uses mutagen when it's installed, which covers MP3/FLAC/OGG/M4A/WMA/APE and
most other common formats through one uniform ``File()`` call. If mutagen
isn't available, every lookup just falls back to a filename-derived title
with empty artist/genre — the player still works, it just shows less in the
"now playing" panel.
"""
from dataclasses import dataclass
from typing import Optional

try:
    import mutagen
    _HAS_MUTAGEN = True
except ImportError:
    _HAS_MUTAGEN = False


@dataclass
class Tags:
    title: str
    artist: str = ""
    genre: str = ""
    album: str = ""
    duration: Optional[float] = None
    bitrate: Optional[int] = None       # bits per second
    sample_rate: Optional[int] = None   # Hz


def _first(easy_tags, *keys):
    for key in keys:
        val = easy_tags.get(key)
        if val:
            return str(val[0])
    return ""


def read_tags(path: str, fallback_title: str) -> Tags:
    if not _HAS_MUTAGEN:
        return Tags(title=fallback_title)
    try:
        audio = mutagen.File(path, easy=True)
    except Exception:
        return Tags(title=fallback_title)
    if audio is None:
        return Tags(title=fallback_title)

    title = _first(audio, "title") or fallback_title
    artist = _first(audio, "artist", "albumartist", "performer")
    genre = _first(audio, "genre")
    album = _first(audio, "album")
    duration = None
    bitrate = None
    sample_rate = None
    info = getattr(audio, "info", None)
    if info is not None and getattr(info, "length", None):
        duration = float(info.length)
    if info is not None and getattr(info, "bitrate", None):
        bitrate = int(info.bitrate)
    if info is not None and getattr(info, "sample_rate", None):
        sample_rate = int(info.sample_rate)

    return Tags(title=title, artist=artist, genre=genre, album=album,
                duration=duration, bitrate=bitrate, sample_rate=sample_rate)
