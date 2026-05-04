from enum import Enum, auto

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