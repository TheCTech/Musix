import spotipy
from spotipy.oauth2 import SpotifyOAuth

import logging

from utils.models import PlayResult, SpotifyTrackData
from utils.utils import get_settings

logger = logging.getLogger(__name__)

scope = "user-modify-playback-state user-read-playback-state"

sp = None

def validate_spotify_token():
    cache_handler = spotipy.CacheFileHandler("cache/spotify_token.json")

    auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json"
        )

    token_info = auth_manager.validate_token(cache_handler.get_cached_token())

    return token_info

def authenticate_spotify():
    auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json"
        )
    SpotifyOAuth.get_access_token(auth_manager)
    logger.debug("Spotify authenticated, token received")

def get_spotify():
    global sp

    if sp is None:
        auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json"
        )

        sp = spotipy.Spotify(auth_manager=auth_manager)

    return sp


def get_active_device_id():
    client = get_spotify()

    devices = client.devices()["devices"]  # type: ignore

    # prefer active device if available
    for d in devices:
        if d.get("is_active"):
            return d["id"]

    logging.debug("No active device found")

    # fallback to last device
    last_device = get_settings().get("last_device")
    if last_device:
        logging.debug("Falling back to the last device")
        if any(device["id"] == last_device for device in devices):
            logging.debug("Fallback successful")
            return last_device

    logger.warning("Could not open any device")
    return None


def set_repeat(state="track", device_id=None):
    client = get_spotify()
    client.repeat(state, device_id=device_id)


def play_song(query) -> tuple[PlayResult, SpotifyTrackData | None]:
    client = get_spotify()

    logger.debug(f"Searching for {query}")

    try:
        results = client.search(q=query, type="track", limit=1)
    except spotipy.SpotifyException as e:
        from utils.ui_utils import show_error
        logger.exception("Spotify error")
        show_error(f"Spotipy error: {e.reason}", notify_support_prompt=True)
        return PlayResult.ERROR, None

    if not results["tracks"]["items"]: # type: ignore
        logger.warning(f"Song not found. ({query})")
        return PlayResult.SONG_NOT_FOUND, None

    track = results["tracks"]["items"][0] # type: ignore
    uri = track["uri"]

    logger.debug(f"Playing: {track['name']} - {track['artists'][0]['name']}")

    device_id = get_active_device_id()

    if not device_id:
        return PlayResult.NO_SPOTIFY, None

    client.start_playback(device_id=device_id, uris=[uri])
    set_repeat(device_id=device_id)

    get_settings().set("last_device", device_id)

    artists = [a["name"] for a in track["artists"]]

    return PlayResult.OK, SpotifyTrackData(track["name"], artists)