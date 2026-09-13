"""Audio CD support.

LibVLC has a built-in "cdda" access module that reads audio CDs directly
(no ripping step) — a URI like ``cdda:///dev/sr0`` (Linux/mac) or
``cdda://D:`` (Windows) is playable through the exact same
``PlayerEngine.load()`` path already used for local files and radio
streams, with no extra plumbing needed there.

What this module adds is *discovery*: given a drive, ask LibVLC to parse
the disc and hand back one playable sub-URI per track (LibVLC exposes each
track of an audio CD as a "subitem" of the disc's own media object). There
is no CDDB/MusicBrainz lookup here, so tracks show up as "Track 01",
"Track 02", etc. rather than with real song titles — wiring up a lookup
service is a reasonable future addition but needs network access and a
disc-identification (TOC hashing) step that's out of scope here.
"""
import os
import sys
import time
from dataclasses import dataclass

import vlc

PARSE_TIMEOUT_S = 4.0


@dataclass
class CDTrack:
    index: int          # 1-based track number
    uri: str             # playable cdda:// MRL for this single track
    duration: float       # seconds, 0.0 if LibVLC couldn't report one


def browse_start_dir() -> str:
    """A reasonable starting folder for a "browse for the CD drive" file
    dialog -- somewhere device nodes or mounted volumes are likely to
    already be visible, per platform, so the user isn't dropped at some
    arbitrary default and left to hunt for the drive themselves."""
    if sys.platform.startswith("win"):
        return ""  # empty starts Qt's dialog at "This PC" / the drive list
    if sys.platform == "darwin":
        return "/Volumes" if os.path.isdir("/Volumes") else "/dev"
    for candidate in ("/media", "/run/media", "/dev"):
        if os.path.isdir(candidate):
            return candidate
    return "/dev"


def _parse_sync(media, timeout_s: float = PARSE_TIMEOUT_S):
    """Parse a vlc.Media synchronously with a timeout. Different python-vlc
    builds expose different parse APIs (older ones only have the blocking
    media.parse(); current ones use the async parse_with_options +
    poll get_parsed_status), so support both rather than assuming one."""
    if hasattr(media, "parse_with_options"):
        try:
            media.parse_with_options(vlc.MediaParseFlag.local, int(timeout_s * 1000))
        except Exception:
            return
        deadline = time.monotonic() + timeout_s
        done_states = {
            getattr(vlc.MediaParsedStatus, "done", 3),
            getattr(vlc.MediaParsedStatus, "failed", 2),
            getattr(vlc.MediaParsedStatus, "timeout", 4),
        }
        while time.monotonic() < deadline:
            try:
                if media.get_parsed_status() in done_states:
                    break
            except Exception:
                break
            time.sleep(0.05)
    elif hasattr(media, "parse"):
        try:
            media.parse()
        except Exception:
            pass


def read_tracks(drive: str, timeout_s: float = PARSE_TIMEOUT_S) -> list["CDTrack"]:
    """Read the track list off the disc in `drive`. Returns an empty list
    (never raises) if there's no disc, no drive, or LibVLC's cdda module
    isn't available on this system — the caller is expected to treat an
    empty result as "nothing found" and degrade gracefully, same as a
    failed skin load elsewhere in this codebase."""
    instance = None
    tracks: list[CDTrack] = []
    try:
        instance = vlc.Instance("--no-video")
        disc_media = instance.media_new(f"cdda://{drive}")
        _parse_sync(disc_media, timeout_s)
        subitems = disc_media.subitems()
        if subitems:
            count = subitems.count()
            for i in range(count):
                item = subitems.item_at_index(i)
                if item is None:
                    continue
                _parse_sync(item, timeout_s=min(1.5, timeout_s))
                dur_ms = item.get_duration()
                duration = dur_ms / 1000.0 if dur_ms and dur_ms > 0 else 0.0
                tracks.append(CDTrack(index=i + 1, uri=item.get_mrl(), duration=duration))
        disc_media.release()
    except Exception:
        return []
    finally:
        if instance is not None:
            instance.release()
    return tracks
