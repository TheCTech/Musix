import os
import json
import re
import logging

logger = logging.getLogger(__name__)


def get_lastfm_username():
    while True:
        username = input("Enter Last.fm username: ").strip()
        if username:
            return username


def normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", text)