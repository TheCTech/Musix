import spotipy
from spotipy.oauth2 import SpotifyOAuth

import logging

from utils.models import PlayResult, SpotifyTrackData
from utils.utils import get_settings
from secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

logger = logging.getLogger(__name__)

scope = "user-modify-playback-state user-read-playback-state"

sp = None

def validate_spotify_token():
    cache_handler = spotipy.CacheFileHandler("cache/spotify_token.json")

    auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json",
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI
        )

    token_info = auth_manager.validate_token(cache_handler.get_cached_token())

    return token_info

def authenticate_spotify():
    auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json",
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI
        )
    
    try:
        token = SpotifyOAuth.get_access_token(auth_manager)

        if not token:
            raise spotipy.exceptions.SpotifyOauthError("No token returned")

        logger.debug("Spotify authenticated, token received")
        return True
    except spotipy.exceptions.SpotifyOauthError as e:
        pass

    from utils.ui_utils import show_error
    logger.error("Failed to authenticate spotify")
    show_error("Failed to authenticate spotify", fatal_error=True) # If user doesn't grant the permission to use spotify the spotipy crashes, you need to restart the app
    return False

def get_spotify():
    global sp

    if sp is None:
        auth_manager = SpotifyOAuth(
            scope=scope,
            cache_path="cache/spotify_token.json",
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI
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


def search_for_track(query) -> tuple[str, SpotifyTrackData] | None:
    client = get_spotify()

    logger.debug(f"Searching for {query}")

    try:
        ### TODO: Fetch more and validate correct title ###
        results = client.search(q=query, type="track", limit=1)
    except spotipy.SpotifyException as e:
        from utils.ui_utils import show_error
        logger.exception("Spotify error")
        show_error(f"Spotipy error: {e.reason}", notify_support_prompt=True)
        return None

    if not results["tracks"]["items"]: # type: ignore
        logger.warning(f"Song not found. ({query})")
        return None

    track = results["tracks"]["items"][0] # type: ignore
    uri = track["uri"]

    logger.debug(f"Found track with name: {track['name']}")

    album_image = track["album"]["images"][0]["url"]

    artists = [a["name"] for a in track["artists"]]

    return (uri, SpotifyTrackData(track["name"], artists, album_image))

def play_song_from_uri(track_uri, track_data):
    logger.debug(f"Playing song from uri: {track_uri}, song data: {track_data.name} {track_data.artists}")

    device_id = get_active_device_id()

    if not device_id:
        return PlayResult.NO_SPOTIFY

    if not get_settings().get("spotify_do_not_disturb_mode"):
        get_spotify().start_playback(device_id=device_id, uris=[track_uri])
        set_repeat(device_id=device_id)

    get_settings().set("last_device", device_id)

    return PlayResult.OK

def get_tracks_from_playlist_or_album(url) -> list[tuple[str, SpotifyTrackData]] | None:
    # https://open.spotify.com/album/3qzrNVuUyOJxfzMYRCh5qN?si=-vm-Zq5vRcegs0vj-CCZXA
    # https://open.spotify.com/playlist/0MjKHGg1tjKMsK6nY5TGad?si=5c50686e9bb34a17

    client = get_spotify()

    if "https://open.spotify.com/album" in url:
        # Album
        album = client.album(url) ### TODO: Fetch more (current max: 50) ###

        assert album is not None

        album_image = album["images"][0]["url"]

        artists = [a["name"] for a in album["artists"]]

        tracks_raw = album["tracks"]["items"]

        tracks = []

        for track_raw in tracks_raw:
            tracks.append((track_raw["uri"], SpotifyTrackData(track_raw["name"], artists, album_image)))
        
        return tracks        

    elif "https://open.spotify.com/playlist" in url:
        # Playlist
        playlist = client.playlist(url[:56][-22:]) ### TODO: Handle the links in a better way ###

        assert playlist is not None

        tracks_raw = playlist["items"]["items"]

        tracks = []

        for track_raw in tracks_raw:
            track_raw = track_raw["item"]
            tracks.append((track_raw["uri"], SpotifyTrackData(track_raw["name"], [a["name"] for a in track_raw["artists"]], track_raw["album"]["images"][0])))

        return tracks 

    else:
        logger.warning(f"Specified album/playlist could not be found, url: {url}")
        from utils.ui_utils import show_error
        show_error("Specified album/playlist could not be found")
        return None