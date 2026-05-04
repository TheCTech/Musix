import spotipy
from spotipy.oauth2 import SpotifyOAuth

import logging

from utils import PlayResult, SpotifyTrackData

logger = logging.getLogger(__name__)

scope = "user-modify-playback-state user-read-playback-state"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def get_active_device_id():
    devices = sp.devices()["devices"] # pyright: ignore[reportOptionalSubscript]

    # prefer active device if available
    for d in devices:
        if d.get("is_active"):
            return d["id"]

    return None

def set_repeat(state="track"):
    sp.repeat(state)


def play_song(query) -> tuple[PlayResult, SpotifyTrackData | None]:
    logger.debug(f"Searching for {query}")
    # search track
    ### TODO: song validation, spotify is dumb ###
    results = sp.search(q=query, type="track", limit=1)

    if not results["tracks"]["items"]: # pyright: ignore[reportOptionalSubscript]
        logger.warning(f"Song not found. ({query})")
        return PlayResult.SONG_NOT_FOUND, None

    track = results["tracks"]["items"][0] # pyright: ignore[reportOptionalSubscript]
    uri = track["uri"]

    logger.debug(f"Playing: {track['name']} - {track['artists'][0]['name']}")

    device_id = get_active_device_id()

    if not device_id:
        logger.warning("Spotify not open")
        return PlayResult.NO_SPOTIFY, None

    sp.start_playback(device_id=device_id, uris=[uri])
    set_repeat()

    artists = []
    for a in track['artists']:
        artists.append(a["name"])

    return PlayResult.OK, SpotifyTrackData(track['name'], artists)