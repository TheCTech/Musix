import random
import logging
from colorlog import ColoredFormatter

from lastfm import get_top_tracks
from spotify import play_song
from utils import (
    PlayResult,
    Settings,
    LastfmTrack,
    SpotifyTrackData,
    TrackAnswerAliases,
    analyze_guess
)


handler = logging.StreamHandler()

formatter = ColoredFormatter(
    "[%(log_color)s%(levelname)s%(reset)s %(name)s]: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
)

handler.setFormatter(formatter)

logger = logging.getLogger()
logger.handlers = []
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Removing libs from logging, leaving only warning and higher level logs
for lib in ["urllib3", "spotipy", "requests"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

settings = Settings()

def guess(lastfm_track: LastfmTrack, spotify_track: SpotifyTrackData):
    answer_aliases = TrackAnswerAliases(lastfm_track, spotify_track)

    title_guessed = False
    artist_guessed = False

    while True:
        logger.debug(f"NAME ALIASES: {answer_aliases.names}")
        logger.debug(f"ARTIST ALIASES: {answer_aliases.artists}")


        print(f"{lastfm_track.name if title_guessed else "XXXX"} by {lastfm_track.artist if artist_guessed else "XXXX"} {"GUESSED!" if artist_guessed and title_guessed else ""}")

        if (artist_guessed and title_guessed):
                ### TODO: scoring system ###
                logger.info("Track guessed")
                return

        user_input = input("ANS: ")

        if user_input == "skip":
            artist_guessed = True
            title_guessed = True

        result = analyze_guess(user_input, answer_aliases)

        logger.debug(f"RESULT: {result}")

        if result["quality"] in ("perfect", "close"):
            if result["match_type"] in ["title", "both"]:
                title_guessed = True
                print("title correct")
            if result["match_type"] in ["artist", "both"]:
                artist_guessed = True
                print("artist correct")


def main():
    top_tracks = get_top_tracks(settings.get("lastfm_username"), limit=settings.get("lastfm_limit")) # type: ignore

    if not top_tracks:
        logger.error("No tracks found.")
        return

    random.shuffle(top_tracks)
    top_tracks = top_tracks[:10]

    for i, track in enumerate(top_tracks):

        logger.debug(f"{track.name} ({i+1}/10)")

        state, spotify_data = play_song(f"track:{track.name} artist:{track.artist}")

        if state == PlayResult.NO_SPOTIFY:
            print("No active Spotify device found. Open Spotify app first.")
            return

        if state == PlayResult.SONG_NOT_FOUND:
            ### TODO: When doing score logic this needs to be taken into account ###
            print("The song could not be found, skipping")
            return

        if state == PlayResult.OK:
            logger.debug("OK (song should be playing)")
            assert spotify_data is not None
            guess(track, spotify_data)


main()