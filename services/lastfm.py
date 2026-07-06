import requests
import logging
import random
from utils.models import SpotifyTrackData
from services.spotify import search_for_track
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

def get_top_tracks(username, period="overall", limit=100, return_amount=10) -> list[tuple[str, SpotifyTrackData]]:
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
    

    logger.debug(f"Got {len(tracks_data)} tracks")
    if len(tracks_data) != limit:
        logger.warning(f"Did not fetch {limit} tracks, possibly not enough data in the selected period?")
    
    random.shuffle(tracks_data)

    tracks = []

    for t_data in tracks_data:
        query = f"track:{t_data['name']} artist:{t_data['artist']['name']}"

        track = search_for_track(query)

        if track == None:
            logger.warning(f"Could not find track using query: {query}")
            continue
            
        assert track is not None

        tracks.append(track)

        if len(tracks) >= return_amount:
            break

    logger.debug(f"Returning {len(tracks)} tracks")

    return tracks