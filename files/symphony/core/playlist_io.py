"""Save/load playlists to disk.

Two formats are supported:

* ``.sympl`` — Symphony's own JSON format. Round-trips everything (artist,
  genre, source, duration) losslessly, including internet radio tracks,
  not just local files.
* ``.m3u`` / ``.m3u8`` — the universal playlist format, for interop with
  other players. Only local file paths and radio/stream URLs survive a
  round trip through M3U (that's a limitation of the format itself, not
  of this code) — extra metadata is written as EXTINF comments on a
  best-effort basis.
"""
import json
import os

from symphony.core.playlist import Track

SYMPL_EXTENSION = ".sympl"


def save_playlist(path: str, tracks: list[Track]):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".m3u", ".m3u8"):
        _save_m3u(path, tracks)
    else:
        if not path.endswith(SYMPL_EXTENSION):
            path += SYMPL_EXTENSION
        _save_sympl(path, tracks)
    return path


def load_playlist(path: str) -> list[Track]:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".m3u", ".m3u8"):
        return _load_m3u(path)
    return _load_sympl(path)


def _save_sympl(path: str, tracks: list[Track]):
    data = {"format": "symphony-playlist", "version": 1,
            "tracks": [t.to_dict() for t in tracks]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _load_sympl(path: str) -> list[Track]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Track.from_dict(d) for d in data.get("tracks", [])]


def _save_m3u(path: str, tracks: list[Track]):
    lines = ["#EXTM3U"]
    for t in tracks:
        secs = int(t.duration) if t.duration else -1
        display = f"{t.artist} - {t.title}" if t.artist else t.title
        lines.append(f"#EXTINF:{secs},{display}")
        lines.append(t.uri)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _load_m3u(path: str) -> list[Track]:
    tracks = []
    pending_title = None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line == "#EXTM3U":
                continue
            if line.startswith("#EXTINF:"):
                _, _, rest = line.partition(",")
                pending_title = rest.strip() or None
                continue
            if line.startswith("#"):
                continue
            uri = line
            is_radio = uri.startswith(("http://", "https://"))
            is_cd = uri.startswith("cdda://")
            title = pending_title or os.path.splitext(os.path.basename(uri))[0]
            artist = ""
            if pending_title and " - " in pending_title:
                artist, _, title = pending_title.partition(" - ")
            tracks.append(Track(
                title=title, artist=artist,
                source="radio" if is_radio else ("cd" if is_cd else "local"),
                uri=uri,
            ))
            pending_title = None
    return tracks
