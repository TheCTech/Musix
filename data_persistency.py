import os
import json
from utils.utils import get_lastfm_username

class Settings:
    FILE = "cache/user_settings.json"
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