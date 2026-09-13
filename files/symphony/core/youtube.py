"""YouTube audio downloads through the optional yt-dlp package.

The player deliberately uses yt-dlp as a library instead of shelling out to a
command copied from a web page.  That keeps cookies, URLs, and progress inside
the app and gives users a clear place to choose the output folder.
"""
import os


def download_audio(
    urls,
    output_dir,
    audio_format="best",
    download_playlists=False,
    progress_callback=None,
):
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "YouTube downloads need yt-dlp. Install the dependencies from "
            "requirements.txt and try again."
        ) from exc

    os.makedirs(output_dir, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        "noplaylist": not download_playlists,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "progress_hooks": [progress_callback] if progress_callback else [],
    }
    if audio_format in ("mp3", "m4a", "opus", "wav"):
        processor = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
        }
        if audio_format == "mp3":
            processor["preferredquality"] = "192"
        options["postprocessors"] = [processor]

    downloaded = []
    with yt_dlp.YoutubeDL(options) as downloader:
        for url in urls:
            info = downloader.extract_info(url, download=True)
            if not info:
                continue
            entries = info.get("entries") or [info]
            for entry in entries:
                if not entry:
                    continue
                requested = entry.get("requested_downloads") or []
                path = None
                if requested:
                    path = requested[0].get("filepath")
                if not path:
                    path = downloader.prepare_filename(entry)
                if audio_format != "best":
                    root, _ = os.path.splitext(path)
                    path = root + "." + audio_format
                if os.path.isfile(path):
                    downloaded.append(os.path.abspath(path))
    return list(dict.fromkeys(downloaded))