"""Best-effort audio tag reading (artist / title / genre / duration).

Uses mutagen when it's installed, which covers MP3/FLAC/OGG/M4A/WMA/APE and
most other common formats through one uniform ``File()`` call. If mutagen
isn't available, every lookup just falls back to a filename-derived title
with empty artist/genre — the player still works, it just shows less in the
"now playing" panel.
"""
import os
import re
from dataclasses import dataclass
from typing import Optional

try:
    import mutagen
    _HAS_MUTAGEN = True
except ImportError:
    _HAS_MUTAGEN = False

try:
    import vlc
    _HAS_VLC = True
except ImportError:
    _HAS_VLC = False

# Filenames are very often "01 - Song Name.mp3" / "01. Song Name.mp3" /
# "01_Song Name.mp3". The playlist already has its own "#" column for the
# track number, so a leading "01 - " baked into the title too is just
# redundant clutter — strip it once, from either a filename-derived title
# or (more rarely) an embedded tag that includes it.
_TRACK_PREFIX_RE = re.compile(r"^\s*\d{1,3}(?:\s*[-._)]\s*|\s+)")

# Generic folder names that are never a real artist name, so a bare
# filename dumped straight in "Music" or "Downloads" doesn't get mislabeled.
_GENERIC_FOLDER_NAMES = {
    "music", "downloads", "download", "desktop", "documents", "my music",
    "songs", "tracks", "audio", "mp3", "media", "playlist", "playlists",
    "new folder", "untitled folder", "home", "shared", "",
}
_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")
_ALBUM_FOLDER_RE = re.compile(
    r"^(?:.*\b(?:edition|bonus|disc|cd|volume|vol\.?)\b.*|"
    r"\s*[\[(](?:19|20)\d{2}[\])].*|\d{1,3})$",
    re.IGNORECASE,
)
_BRACKET_YEAR_ALBUM_RE = re.compile(
    r"^\s*[\[(](?:19|20)\d{2}[\])]\s*(.*?)\s*$"
)

# A folder is very often named "Artist - Album" (or "Artist – Album (Year)")
# rather than just the artist, e.g. a ripped album/mixtape folder. Split on
# the dash so "Lloyd Banks - Return Of The PLK" yields an artist AND an
# album instead of dumping the whole folder name into the artist field.
_FOLDER_SPLIT_RE = re.compile(r"^\s*(.+?)\s+[-\u2013\u2014]\s+(.+?)\s*$")


def strip_track_prefix(title: str) -> str:
    cleaned = _TRACK_PREFIX_RE.sub("", title, count=1).strip()
    return cleaned or title


def guess_artist_album_from_path(path: str):
    """When a file has no artist/album tags, its containing folder is very
    often "Artist" or "Artist - Album" (a common convention for organizing
    untagged rips). Returns (artist, album); either may be "" when nothing
    usable can be guessed, rather than showing something misleading."""
    folder_path = os.path.dirname(os.path.abspath(path))
    folder = os.path.basename(folder_path)
    if folder.lower() in _GENERIC_FOLDER_NAMES or _YEAR_RE.fullmatch(folder.strip()):
        return _find_parent_artist(folder_path), ""
    match = _FOLDER_SPLIT_RE.match(folder)
    if match:
        artist, album = match.group(1).strip(), match.group(2).strip()
        if not _looks_like_year(artist):
            return artist, album
        return _find_parent_artist(folder_path), album
    if _ALBUM_FOLDER_RE.match(folder) or _looks_like_year(folder):
        bracket_album = _BRACKET_YEAR_ALBUM_RE.match(folder)
        album = bracket_album.group(1).strip() if bracket_album else ""
        return _find_parent_artist(folder_path), album
    return folder, ""


def _find_parent_artist(folder_path: str) -> str:
    """Find an artist directory above year/edition/disc directories."""
    current = os.path.abspath(folder_path)
    home = os.path.abspath(os.path.expanduser("~"))
    for _ in range(5):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
        # The user's home directory is a container, not an artist folder.
        # Without this guard a path such as /home/jaco/2008/song.mp3
        # incorrectly turns "jaco" into the artist.
        if current == home:
            break
        name = os.path.basename(current).strip()
        if (
            not name
            or name.lower() in _GENERIC_FOLDER_NAMES
            or _YEAR_RE.fullmatch(name)
            or _ALBUM_FOLDER_RE.match(name)
        ):
            continue
        match = _FOLDER_SPLIT_RE.match(name)
        candidate = match.group(1).strip() if match else name
        if candidate and not _looks_like_year(candidate):
            return candidate
    return ""


def guess_artist_from_path(path: str) -> str:
    return guess_artist_album_from_path(path)[0]


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


def _all(easy_tags, *keys):
    """Return all values for a tag, preserving multi-artist metadata."""
    for key in keys:
        values = easy_tags.get(key)
        if values:
            if isinstance(values, (str, bytes)):
                values = [values]
            cleaned = [str(value).strip() for value in values if str(value).strip()]
            if cleaned:
                return ", ".join(dict.fromkeys(cleaned))
    return ""


def _looks_like_year(value: str) -> bool:
    return bool(_YEAR_RE.fullmatch((value or "").strip()))


def _looks_like_home_name(value: str) -> bool:
    home_name = os.path.basename(os.path.abspath(os.path.expanduser("~")))
    return bool(value) and value.strip().casefold() == home_name.casefold()


def _clean_artist(value: str) -> str:
    """Remove accidental track-number prefixes from artist tags too."""
    return strip_track_prefix((value or "").strip())


def _guess_artist_from_filename(path: str) -> str:
    """Use ``Artist - Title`` filenames as a last-resort artist fallback."""
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = strip_track_prefix(stem)
    parts = re.split(r"\s+[-\u2013\u2014]\s+", stem, maxsplit=1)
    if len(parts) != 2:
        return ""
    artist = parts[0].strip()
    if not artist or _looks_like_year(artist):
        return ""
    return artist


def read_duration(path: str) -> Optional[float]:
    """Read duration independently of the user's tag-display preference."""
    if _HAS_MUTAGEN:
        try:
            audio = mutagen.File(path)
            info = getattr(audio, "info", None)
            length = getattr(info, "length", None)
            if length:
                return float(length)
        except Exception:
            pass

    # VLC is already a required playback dependency. Use its demuxer as a
    # fallback for formats or files that Mutagen cannot inspect.
    if _HAS_VLC:
        instance = media = None
        try:
            instance = vlc.Instance("--no-video", "--quiet")
            media = instance.media_new(path)
            media.parse()
            length_ms = media.get_duration()
            if length_ms and length_ms > 0:
                return float(length_ms) / 1000.0
        except Exception:
            pass
        finally:
            try:
                if media is not None:
                    media.release()
                if instance is not None:
                    instance.release()
            except Exception:
                pass
    return None


def read_tags(path: str, fallback_title: str) -> Tags:
    fallback_title = strip_track_prefix(fallback_title)
    folder_artist, folder_album = guess_artist_album_from_path(path)
    filename_artist = _guess_artist_from_filename(path)
    if not _HAS_MUTAGEN:
        return Tags(
            title=fallback_title,
            artist=folder_artist or filename_artist,
            album=folder_album,
        )
    try:
        audio = mutagen.File(path, easy=True)
    except Exception:
        return Tags(
            title=fallback_title,
            artist=folder_artist or filename_artist,
            album=folder_album,
        )
    if audio is None:
        return Tags(
            title=fallback_title,
            artist=folder_artist or filename_artist,
            album=folder_album,
        )

    title = strip_track_prefix(_first(audio, "title") or fallback_title)
    artist = _clean_artist(_all(audio, "artist", "performer"))
    album_artist = _clean_artist(_all(audio, "albumartist"))
    # Some rips put the release year in the artist field. Do not let that
    # shadow a real album artist or turn a year-named folder into an artist.
    if _looks_like_year(artist) or _looks_like_home_name(artist):
        artist = ""
    if not artist:
        artist = album_artist
    if _looks_like_year(artist) or _looks_like_home_name(artist):
        artist = ""
    artist = artist or folder_artist or filename_artist
    genre = _first(audio, "genre")
    album = _first(audio, "album") or folder_album
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

