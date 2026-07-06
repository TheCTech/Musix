from enum import Enum, auto

class PlayResult(Enum):
    OK = auto()
    SONG_NOT_FOUND = auto()
    NO_SPOTIFY = auto()
    ERROR = auto()


class SpotifyTrackData:
    def __init__(self, name, artists, image_url):
        self.name = name
        self.artists = artists
        self.image_url = image_url