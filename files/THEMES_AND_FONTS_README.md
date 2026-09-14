# Symphony Audio Player - Themes and Fonts Configuration

## 1. Switching Default Themes (Dark & Light)
Symphony comes with two built-in modern themes:
- Dark Mode: Deep slate and obsidian backgrounds with electric cobalt accents.
- Light Mode: Clean daylight neutrals with crisp contrast and royal blue accents.

### How to Switch:
1. Click OPTIONS in the top right.
2. Select Preferences….
3. Under the Theme section, select either 'dark' or 'light'.
4. Click Save to immediately apply the theme.

---

## 2. Disabling Skins (Using Default Theme)
If a Winamp classic skin (.wsz) is loaded and you want to return to the clean, modern default player look:
1. Click OPTIONS in the top right.
2. Select Disable Skin (Use Default Theme).
3. The player immediately clears skin bitmaps, restores clean beveled buttons, and applies your active theme.

---

## 3. Configuring Custom Fonts
You can configure any system font and font size for Symphony's UI:
1. Open config.json (located in your Symphony configuration directory).
2. Update or add the following keys:
   {
       "ui_font_family": "Inter",
       "ui_font_size": 11
   }

   Recommended modern fonts:
   - Linux: Inter, Ubuntu, DejaVu Sans, Cantarell, Noto Sans
   - Windows: Segoe UI, Segoe UI Variable, Aptos
   - macOS: SF Pro Display, Helvetica Neue

---

## 4. Loading Classic Winamp Skins (.wsz)
1. Click OPTIONS -> Load Skin (.wsz)….
2. Select any classic Winamp .wsz skin archive.
3. Symphony loads the skin artwork while keeping the transport buttons wide, sharp, and easy to read.

---

## 5. Playlist Right-Click Menu
Right-click anywhere inside the PLAYLIST EDITOR window to access quick shortcuts:
- Add File(s)…: Browse and add individual audio files.
- Add Folder…: Import entire music folders.
- Remove Selected Track: Remove the highlighted song.
- Clear Playlist: Empty the current playlist.
