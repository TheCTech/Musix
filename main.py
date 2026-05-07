from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

import sys
import os
import logging
from colorlog import ColoredFormatter
from threading import Thread

from game_logic import GuessScreen, play
from utils.ui_utils import LoadingScreen


#region setup
os.makedirs("cache", exist_ok=True) # Create cache folder for saving data

handler = logging.StreamHandler(sys.stdout)

formatter = ColoredFormatter(
    "[%(log_color)s%(levelname)s%(reset)s %(name)s]: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
)

handler.setFormatter(formatter)

logger = logging.getLogger()
logger.handlers = []
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Removing libs from logging, leaving only warning and higher level logs
for lib in ["urllib3", "spotipy", "requests"]:
    logging.getLogger(lib).setLevel(logging.WARNING)
#endregion
 
class MusixApp(App):
    def build(self):
        self.sm = ScreenManager()

        self.loading_screen = LoadingScreen(name="loading_screen")
        self.sm.add_widget(self.loading_screen)

        self.guess_screen = GuessScreen(name="guess_screen")
        self.sm.add_widget(self.guess_screen)

        self.sm.current = "loading_screen"

        return self.sm

    def on_start(self):
        Thread(target=play, args=(self.sm,), daemon=True).start()


if __name__ == "__main__":
    MusixApp().run()