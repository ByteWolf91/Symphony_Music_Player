"""Internet radio support.

Station discovery uses the community-run, free, keyless Radio Browser API
(https://www.radio-browser.info), which indexes tens of thousands of live
internet radio streams worldwide. A station's ``url_resolved`` is a direct
stream URL that LibVLC can play exactly like a local file — no special
handling needed anywhere else in the app once it's in the playlist as a
Track(source="radio").

A user can also always add a station by pasting a raw stream URL directly,
which needs no network call at all.
"""
from dataclasses import dataclass

import requests

# Several mirrors exist; try in order so one mirror being down doesn't break
# the feature. (There's a DNS-SRV based "all.api.radio-browser.info" that's
# meant to auto-resolve to a healthy mirror, but a small fixed fallback list
# is simpler and doesn't add a DNS-SRV dependency.)
API_MIRRORS = [
    "https://de1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
]

HEADERS = {"User-Agent": "Symphony-Music-Player/1.1"}


@dataclass
class RadioStation:
    name: str
    url: str
    tags: str
    country: str
    codec: str
    bitrate: int


def _get(endpoint: str, params: dict) -> list:
    last_error = None
    for base in API_MIRRORS:
        try:
            resp = requests.get(f"{base}{endpoint}", params=params,
                                 headers=HEADERS, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"Couldn't reach the radio directory: {last_error}")


def search(query: str = "", tag: str = "", limit: int = 30) -> list[RadioStation]:
    params = {
        "limit": limit,
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true",
    }
    if query:
        params["name"] = query
    if tag:
        params["tag"] = tag
    data = _get("/json/stations/search", params)
    stations = []
    for item in data:
        url = item.get("url_resolved") or item.get("url")
        if not url:
            continue
        stations.append(RadioStation(
            name=item.get("name", "Unknown station").strip() or "Unknown station",
            url=url,
            tags=item.get("tags", ""),
            country=item.get("country", ""),
            codec=item.get("codec", ""),
            bitrate=item.get("bitrate", 0) or 0,
        ))
    return stations


def top_stations(limit: int = 30) -> list[RadioStation]:
    return search(query="", limit=limit)
