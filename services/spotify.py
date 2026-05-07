import spotipy
from spotipy.oauth2 import SpotifyOAuth

import logging

from utils.models import PlayResult, SpotifyTrackData
from data_persistency import Settings

logger = logging.getLogger(__name__)

scope = "user-modify-playback-state user-read-playback-state"

sp = None

settings = None

def get_settings():
    global settings
    if settings is None:
        settings = Settings()
    return settings

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
    print(SpotifyOAuth.get_access_token(auth_manager))

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
        return last_device

    logger.warning("Could not open any device")
    return None


def set_repeat(state="track", device_id=None):
    client = get_spotify()
    client.repeat(state, device_id=device_id)  # type: ignore


def play_song(query) -> tuple[PlayResult, SpotifyTrackData | None]:
    client = get_spotify()

    logger.debug(f"Searching for {query}")

    results = client.search(q=query, type="track", limit=1)  # type: ignore

    if not results["tracks"]["items"]: # type: ignore
        logger.warning(f"Song not found. ({query})")
        return PlayResult.SONG_NOT_FOUND, None

    track = results["tracks"]["items"][0] # type: ignore
    uri = track["uri"]

    logger.debug(f"Playing: {track['name']} - {track['artists'][0]['name']}")

    device_id = get_active_device_id()

    if not device_id:
        return PlayResult.NO_SPOTIFY, None

    client.start_playback(device_id=device_id, uris=[uri])  # type: ignore
    set_repeat(device_id=device_id)

    get_settings().set("last_device", device_id)

    artists = [a["name"] for a in track["artists"]]

    return PlayResult.OK, SpotifyTrackData(track["name"], artists)