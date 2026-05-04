import re
from utils.utils import normalize
from utils.models import LastfmTrack, SpotifyTrackData

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