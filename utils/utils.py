import re
import logging
from kivy.app import App
from kivy.clock import Clock

from threading import Thread

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

def handle_spotify_authentication_button(is_spotify, button_instance): # False for connect True for disconnect
    app = get_app()
    Clock.schedule_once(lambda dt: setattr(app.sm, "current", "loading_screen"))
    
    def main_logic():
        if not is_spotify:
            logger.debug("Trying to authenticate spotify")
            from services.spotify import authenticate_spotify
            authenticate_spotify()
        else:
            logger.debug("Removing spotify token from cache")
            from os import remove
            remove("cache/spotify_token.json")

            app.home_screen.play_button.disabled = True
            app.home_screen.validate_spotify()
        
        
        button_instance.text = "Connect" if is_spotify else "Disconnect"

        Clock.schedule_once(lambda dt: setattr(app.sm, "current", "settings_screen")) # In general changing ui from background thread is a bad practice but with loading screen it should,'t be such a big deal, right? :)

    Thread(target=main_logic, daemon=True).start()