import os
import json
import re
import logging
from enum import Enum, auto
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class PlayResult(Enum):
    OK = auto()
    SONG_NOT_FOUND = auto()
    NO_SPOTIFY = auto()


class LastfmTrack:
    def __init__(self, name, artist, playcount):
        self.name = name
        self.artist = artist
        self.playcount = playcount


class SpotifyTrackData:
    def __init__(self, name, artists):
        self.name = name
        self.artists = artists

class TrackAnswerAliases:
    def __init__(self, lastfm_track: LastfmTrack, spotify_track: SpotifyTrackData):

        title_variants = set()
        artist_variants = set()
        both_variants = set()

        # title variants
        title_variants.update(split_title_variants(lastfm_track.name))
        title_variants.update(split_title_variants(spotify_track.name))

        # artist variants
        for a in [lastfm_track.artist, *spotify_track.artists]:
            artist_variants.add(normalize(a))

        # merged variants
        for t in title_variants:
            for a in artist_variants:
                both_variants.add(t + a)
                both_variants.add(a + t)

        # "return"
        self.names = list(title_variants)
        self.artists = list(artist_variants)
        self.both = list(both_variants)


def get_lastfm_username():
    while True:
        username = input("Enter Last.fm username: ").strip()
        if username:
            return username


class Settings:
    FILE = "settings.json"
    DEFAULTS = {
        "lastfm_limit": 100,
        "lastfm_period": "overall"
    }

    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(self.FILE):
            self.save(self.DEFAULTS)
            return self.DEFAULTS.copy()

        with open(self.FILE, "r") as f:
            data = json.load(f)

        for key, value in self.DEFAULTS.items():
            data.setdefault(key, value)

        return data

    def save(self, data=None):
        if data is not None:
            self.data = data

        with open(self.FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key):
        if key in self.data:
            return self.data[key]

        if key == "lastfm_username":
            username = get_lastfm_username()
            self.set("lastfm_username", username)
            return username

        return None

    def set(self, key, value):
        self.data[key] = value
        self.save()

def normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", text)



def analyze_guess(user_input: str, answer_aliases: TrackAnswerAliases):
    user_input = normalize(user_input)

    scores: list[tuple[str, float]] = []
    for artist in answer_aliases.artists:
        scores.append(("artist", fuzz.ratio(user_input, artist)))
    for title in answer_aliases.names:
        scores.append(("title", fuzz.ratio(user_input, title)))
    for both in answer_aliases.both:
        scores.append(("both", fuzz.ratio(user_input, both)))

    logger.debug(scores)

    best = max(scores, key=lambda x: x[1])

    best_type = best[0]
    best_score = best[1]

    if best_score >= 90:
        quality = "perfect"
    elif best_score >= 75:
        quality = "close"
    elif best_score >= 50:
        quality = "partial"
    else:
        quality = "bad"

    return {
        "match_type": best_type,
        "score": round(best_score, 2),
        "quality": quality
    }

def split_title_variants(text: str) -> list[str]:
    text = text.lower()


    # literal magic, dont touch will break
    no_remaster = re.sub(r"\s*remaster.*$", "", text)
    no_dash = re.sub(r"\s*-.*$", "", no_remaster)

    inside = re.findall(r"\((.*?)\)", no_dash)
    base = re.sub(r"\(.*?\)", "", no_dash)

    base_clean = normalize(base)
    extras = [normalize(x) for x in inside]

    variants = set()

    if base_clean:
        variants.add(base_clean)

    for e in extras:
        if e:
            variants.add(e)
            variants.add(base_clean + e)

    if not variants:
        variants.add(normalize(text))

    return list(variants)