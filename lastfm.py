import requests
import dotenv
import logging
from utils import LastfmTrack

logger = logging.getLogger(__name__)

LASTFM_API_KEY = dotenv.get_key(".env", "LASTFM_API_KEY")

def get_top_tracks(username, period="overall", limit=1) -> list[LastfmTrack]:
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

    return tracks