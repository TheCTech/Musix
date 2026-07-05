import re
import logging

from utils.utils import normalize
from utils.models import LastfmTrack, SpotifyTrackData

logger = logging.getLogger(__name__)

NOISE_PATTERNS = [
    r"\s*\(.*?remaster.*?\)",
    r"\s*\(.*?remastered.*?\)",
    r"\s*\(.*?radio edit.*?\)",
    r"\s*\(.*?live.*?\)",
    r"\s*-\s*(remaster|remastered|radio edit|live)\b.*$",
]

def strip_noise(text: str) -> str:
    text = text.lower()
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()


def split_title_variants(text: str) -> list[str]:
    text = text.lower()
    text = strip_noise(text)

    # split on parentheses content
    inside = re.findall(r"\((.*?)\)", text)
    base = re.sub(r"\(.*?\)", "", text)

    base_clean = normalize(base)
    extras = [normalize(x) for x in inside]

    variants = set()

    if base_clean:
        variants.add(base_clean)

    for e in extras:
        if e:
            variants.add(e)
            if base_clean:
                variants.add(base_clean + e)

    # IMPORTANT: keep dash-split candidates instead of deleting them
    dash_parts = [p.strip() for p in re.split(r"\s*-\s*", text) if p.strip()]
    for part in dash_parts:
        norm = normalize(part)
        if norm:
            variants.add(norm)

    if not variants:
        variants.add(normalize(text))

    return list(variants)

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

        logger.debug(f"NAME ALIASES: {self.names}")
        logger.debug(f"ARTIST ALIASES: {self.artists}")