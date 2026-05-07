import os
import json
import re
import logging
from typing import cast
from kivy.app import App

logger = logging.getLogger(__name__)


def get_app() -> App:
    app = App.get_running_app()
    assert app is not None
    return cast(App, app)

def get_lastfm_username():
    while True:
        username = input("Enter Last.fm username: ").strip()
        if username:
            return username


def normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", text)