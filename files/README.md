# Symphony

A classic-Winamp-style desktop music player, written in Python (PyQt5 + LibVLC).

Real `.wsz` skin support, a VLC-backed engine that plays essentially any audio
format your system's LibVLC install supports, built-in internet radio (via
the free Radio-Browser directory), audio CD playback, and optional YouTube
audio downloads.

## 1. Install system dependencies

Symphony plays audio through **LibVLC**, so the VLC app itself must be
installed on your system (the `python-vlc` package is just bindings — it
needs the real VLC libraries to talk to):

- **macOS**: `brew install --cask vlc`
- **Windows**: install VLC from https://www.videolan.org/vlc/ (use the same
  bitness — 64-bit VLC for 64-bit Python)
- **Linux**: `sudo apt install vlc` (Debian/Ubuntu) or your distro's equivalent

## 2. Install Python dependencies

Use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Metadata tagging (artist/title/genre in the now-playing display) uses
`mutagen`. YouTube audio downloads use `yt-dlp`; MP3/M4A/Opus conversion also
needs FFmpeg, while "Best available audio" works without conversion.

## 3. Run it

```bash
python main.py
```

## 4. Sources

### Internet Radio
**Options → Internet Radio…** (or the **★ RADIO STATIONS** button in the
Playlist window) — search or browse live stations from the free, keyless
Radio-Browser directory, or paste any direct stream URL. Stations can be
saved to Favorites for quick access later — the **★ RADIO STATIONS** button
in the Playlist window jumps straight to your saved list, and the Favorites
tab in the Internet Radio dialog is always shown first, with a live count
(e.g. "★ Favorites (3)"). Radio tracks already in the playlist also get
their own "📻 Radio Stations" section in the Playlist window, separate from
local files, so a saved/queued station is easy to spot and jump back to.

### Audio CD
The Playlist window has one **SELECT CD DRIVE…** action. Pick the optical
drive/device in the file manager and Symphony adds the disc's tracks to the
playlist. There are no separate "play now", auto-detect, or manual path-entry
variants. Tracks are read through LibVLC's CDDA support and show up as
"Track 01", "Track 02", etc.

### YouTube audio
In the Playlist window choose **YOUTUBE AUDIO…**, paste one or more video URLs,
choose a download folder, and optionally download an entire YouTube playlist.
"Best available audio" avoids conversion; MP3/M4A/Opus options use FFmpeg.
Finished files are added to the current playlist automatically.

## 5. Load a classic Winamp skin

Symphony ships with the **base-2.91** classic Winamp skin bundled in and set
as the out-of-the-box default look — no setup needed to get a fully skinned
player on first launch.

**Options → Load Skin (.wsz)…** — pick any other classic Winamp 2.x `.wsz`
skin file to switch. Symphony unzips it and re-skins the main window,
buttons, LCD digits, EQ window, and playlist colors from the real sprite
sheets. This is a best-effort renderer, not a pixel-perfect implementation of
the full skin spec (that's a years-long project — see the open-source
**Webamp** project if you want that level of fidelity) — but it will look and
feel like the real skin. Whatever skin you load last is remembered and
restored on the next launch (**Options → Preferences → Interface → "Restore
the last skin on startup"**).

## 6. Light / dark theme

**Options → Preferences → Interface → Theme** — switch between a dark and a
light classic-Winamp-ish theme. Applies immediately.

## Mouse controls

Besides the usual clicks and drags:

- **Scroll wheel over the volume slider** — adjusts volume up/down.
- **Scroll wheel over the duration/seek bar** — seeks through the current
  track without needing to drag the handle.
- **⏪ / ⏩ seek buttons** (next to Play/Pause) — a tap seeks 5s; keep the
  button held down and it ramps up to 10s per step the longer you hold it,
  so small corrections stay small and long holds cover ground faster.

## Keyboard shortcuts

| Key | Action |
|---|---|
| Space | Play / Pause |
| N | Skip to next track |
| B | Skip to previous track |
| F | Seek forward 10s |
| D | Seek backward 10s |
| S | Toggle shuffle |
| R | Toggle repeat |
| + / = | Volume up |
| - | Volume down |
| M | Add music folder |
| Ctrl+E / Ctrl+L | Toggle Equalizer / Playlist window |
| Ctrl+← / Ctrl+→ | Balance left / right |
| Up / Down / Page Up / Page Down / Enter | Navigate & play in the playlist window |
| Delete | Remove selected playlist item |
| Q | Quit |

(Also viewable any time from **Options → Keyboard Shortcuts…**.)

## Project layout

```
symphony/
  core/      playback engine, playlist model, playlist save/load, skin parser, radio directory, audio CD reader
  ui/        PyQt5 windows and custom-drawn widgets
  skins/     bundled default .wsz skin (base-2.91)
main.py
```
