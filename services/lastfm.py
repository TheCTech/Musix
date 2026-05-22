import requests
import logging
from utils.models import LastfmTrack
from secrets import LASTFM_API_KEY

logger = logging.getLogger(__name__)


def verify_user(username):
    logger.debug(f"Verifying user \"{username}\" exists on lastfm")
    r = requests.get(
        "http://ws.audioscrobbler.com/2.0/",
        params={
            "method": "user.getinfo",
            "user": username,
            "api_key": LASTFM_API_KEY,
            "format": "json"
        }
    )
    data = r.json()

    if "user" in data.keys():
        logger.debug("Client exists")
        return True
    
    logger.warning(f"User not found, error code: {data['error']}")
    return False

def get_top_tracks(username, period="overall", limit=100) -> list[LastfmTrack]:
    logger.debug(f"Searching user {username}'s top tracks with settings: period={period}, limit={limit}")
    r = requests.get(
        "http://ws.audioscrobbler.com/2.0/",
        params={
            "method": "user.getTopTracks",
            "user": username,
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "period": period,
            "limit": limit
        }
    )
    data = r.json()
    tracks_data = data["toptracks"]["track"]

    # handle single-track edge case
    if isinstance(tracks_data, dict):
        tracks_data = [tracks_data]

    tracks = []

    for t in tracks_data:
        tracks.append(
            LastfmTrack(
                name=t["name"],
                artist=t["artist"]["name"],
                playcount=int(t["playcount"])
            )
        )

    logger.debug(f"Got {len(tracks)} tracks")
    if len(tracks) != limit:
        logger.warning(f"Did not fetch {limit} tracks, possibly not enough data in the selected period?")

    return tracks