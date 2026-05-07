import os
import json
import re
import logging
from typing import cast
from kivy.app import App

logger = logging.getLogger(__name__)

app: App | None = None

def get_app() -> App:
    global app
    if app is None:
        app = App.get_running_app()
        
    return app

def get_settings():
    return get_app().settings_obj

def get_lastfm_username():
    while True:
        username = input("Enter Last.fm username: ").strip()
        if username:
            return username


def normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", text)