import re
import logging
from typing import Any
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager

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
            sp_auth_return = authenticate_spotify()

            if not sp_auth_return:
                button_instance.text = "ERROR"
                return # Do not continue

            button_instance.text = "Disconnect"
        else:
            logger.debug("Removing spotify token from cache")
            from os import remove
            remove("cache/spotify_token.json")

            app.home_screen.play_button.disabled = True
            app.home_screen.validate_spotify()

            button_instance.text = "Connect"

        Clock.schedule_once(lambda dt: setattr(app.sm, "current", "settings_screen")) # In general changing ui from background thread is a bad practice but with loading screen it should,'t be such a big deal, right? :)

    Thread(target=main_logic, daemon=True).start()

class LockableScreenManager(ScreenManager):
    _locked = False
    
    def lock(self):
        logger.debug("Locking screen manager")
        self._locked = True
    
    def __setattr__(self, name, value):
        if name == "current" and self._locked == True:
            logger.warning("Tried to change screen when screen manager was locked")
            return
        super().__setattr__(name, value)