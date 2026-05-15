from kivy.app import App

import sys
import os
import logging
from colorlog import ColoredFormatter

from game_logic import GuessScreen
from utils.ui_utils import LoadingScreen, HomeScreen, ErrorScreen, SettingsScreen, show_error
from utils.utils import LockableScreenManager
from data_persistency import Settings

from logging.handlers import RotatingFileHandler


#region setup
os.makedirs("cache", exist_ok=True) # Create cache folder for saving data
os.makedirs("logs", exist_ok=True) # Create logs folder for storing logs

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

file_handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=2_000_000,
    backupCount=3,
    encoding="utf-8"
)

file_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s %(name)s]: %(message)s"
)

file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)

# Removing libs from logging, leaving only warning and higher level logs
for lib in ["urllib3", "spotipy", "requests"]:
    logging.getLogger(lib).setLevel(logging.WARNING)


def handle_exception(exc_type, exc_value, exc_traceback):
    logging.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

    try:
        os.makedirs("cache", exist_ok=True)
        with open("cache/crash.flag", "w", encoding="utf-8") as f:
            f.write("crash detected")
    except Exception:
        logging.error("Failed to write crash flag")
        pass # Do not crash in the crash handler

sys.excepthook = handle_exception
#endregion
 
class MusixApp(App):
    def build(self):
        self.check_if_reopen_after_crash()
    
        self.settings_obj = Settings()

        self.sm = LockableScreenManager()

        self.home_screen = HomeScreen(name="home_screen")
        self.sm.add_widget(self.home_screen)

        self.settings_screen = SettingsScreen(name="settings_screen")
        self.sm.add_widget(self.settings_screen)

        self.loading_screen = LoadingScreen(name="loading_screen")
        self.sm.add_widget(self.loading_screen)

        self.error_screen = ErrorScreen(name="error_screen", error_text="")
        self.sm.add_widget(self.error_screen)

        self.guess_screen = GuessScreen(name="guess_screen")
        self.sm.add_widget(self.guess_screen)

        self.sm.current = "home_screen"

        if self._previous_crash:
            message = (
                "The app closed unexpectedly last time.\n"
                "If this keeps happening, check logs or contact support."
            )
            show_error(message)

        return self.sm

    def check_if_reopen_after_crash(self):
        if os.path.exists("cache/crash.flag"):
            logger.warning("Previous crash detected")

            self._previous_crash = True

            os.remove("cache/crash.flag")
        else:
            self._previous_crash = False


if __name__ == "__main__":
    logger.info("APP STARTING")
    MusixApp().run()