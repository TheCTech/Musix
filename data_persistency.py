import os
import json
import logging
from utils.utils import get_storage_path

logger = logging.getLogger(__name__)

class Settings:
    FILE = None
    DEFAULTS = {
        "round_length": 10,
        "input_autofocus": True,
        "lastfm_limit": 100,
        "lastfm_period": "overall",
        "lastfm_username": "",
        "gamemode": "lastfm",
        "spotify_playlist_url": "",
        "spotify_album_url": "",

        "debug_mode": True, ### TODO: Change default debug_mode to False ###
        "spotify_do_not_disturb_mode": False
    }

    ### TODO: Store only changed settings ###

    def __init__(self):
        self.FILE = f"{get_storage_path()}/cache/user_settings.json"
        self.data = self.load()

    def load(self):
        assert self.FILE is not None
        
        if not os.path.exists(self.FILE):
            self.save(self.DEFAULTS)
            return self.DEFAULTS.copy()

        with open(self.FILE, "r") as f:
            data = json.load(f)

        for key, value in self.DEFAULTS.items():
            data.setdefault(key, value)

        return data

    def save(self, data=None):
        assert self.FILE is not None

        if data is not None:
            self.data = data

        with open(self.FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key):
        if key in self.data:
            return self.data[key]

        logger.warning(f"Trying to get \"{key}\", but the key does not exist")
        return None

    def set(self, key, value):
        self.data[key] = value
        self.save()