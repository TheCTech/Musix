from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen

import logging
import random

from services.lastfm import get_top_tracks, verify_user
from services.spotify import play_song, PlayResult
from matching.aliases import TrackAnswerAliases
from matching.matching import analyze_guess
from utils.utils import get_app, get_settings
from utils.ui_utils import show_error

logger = logging.getLogger(__name__)

class GuessScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ready = False

        layout = BoxLayout(orientation="vertical")

        self.label = TextInput(readonly=True)
        layout.add_widget(self.label)

        self.input_bar = TextInput(
            multiline=False,
            on_text_validate=self.on_text_enter
        )
        layout.add_widget(self.input_bar)

        self.add_widget(layout)

    def start_guessing(self, lastfm_track, spotify_track):
        self.lastfm_track = lastfm_track
        self.spotify_track = spotify_track

        self.answer_aliases = TrackAnswerAliases(lastfm_track, spotify_track)

        self.title_guessed = False
        self.artist_guessed = False

        self.update_display()

        self.ready = True

    def on_text_enter(self, instance):
        user_input = instance.text.strip()
        instance.text = ""

        if not self.ready:
            return

        if user_input == "skip":
            self.title_guessed = True
            self.artist_guessed = True
            self.finish()
            return

        result = analyze_guess(user_input, self.answer_aliases)

        if result["quality"] in ("perfect", "close"):
            if result["match_type"] in ["title", "both"]:
                self.title_guessed = True
            if result["match_type"] in ["artist", "both"]:
                self.artist_guessed = True

        if self.title_guessed and self.artist_guessed:
            self.finish()
        else:
            self.update_display()

    def update_display(self):
        title = self.lastfm_track.name if self.title_guessed else "XXXX"
        artist = self.lastfm_track.artist if self.artist_guessed else "XXXX"

        self.label.text = f"{title} by {artist}"
    
    def finish(self):
        self.label.text = f"{self.lastfm_track.name} by {self.lastfm_track.artist} YEEEH"

        self.current_track_id += 1
        if self.current_track_id > len(self.tracks)-1:
            Clock.schedule_once(lambda dt: setattr(get_app().sm, "current", "home_screen"), 0) 
            return
        ### TODO: scoring###

        Clock.schedule_once(lambda dt: self.prepare_round(), 5) 
    
    def prepare_round(self):
        track = self.tracks[self.current_track_id]

        logger.debug(f"{track.name} ({self.current_track_id+1}/{len(self.tracks)})")

        state, spotify_data = play_song(f"track:{track.name} artist:{track.artist}")

        if state == PlayResult.NO_SPOTIFY:
            print("No active Spotify device found. Open Spotify app first.")
            show_error("No active Spotify device found. Open Spotify app first.")
            return

        if state == PlayResult.ERROR:
            logger.error("Round preparation cancelled, spotify error detected")
            # The error should be handled externally
            return

        if state == PlayResult.SONG_NOT_FOUND:
            ### TODO: When doing score logic this needs to be taken into account ###
            print("The song could not be found, skipping")
            show_error("The song could not be found")
            return

        if state == PlayResult.OK:
            logger.debug("OK (song should be playing)")
            assert spotify_data is not None
            self.start_guessing(track, spotify_data)

    def prepare_game(self, tracks):
        self.tracks = tracks
        self.current_track_id = 0

        self.prepare_round()


def play(): 
    sm: ScreenManager = get_app().sm

    Clock.schedule_once(lambda dt: setattr(sm, "current", "loading_screen"), 0)

    guess_screen: GuessScreen = sm.get_screen("guess_screen")

    settings = get_settings()

    lastfm_username = settings.get("lastfm_username")

    if not verify_user(lastfm_username):
        show_error("Last.fm user not found, please specify the correct username in settings")

    top_tracks = get_top_tracks(lastfm_username, limit=settings.get("lastfm_limit"))

    if not top_tracks:
        logger.error("No tracks found.")
        show_error("Could not fetch any tracks")
        return

    random.shuffle(top_tracks)
    top_tracks = top_tracks[:get_settings().get("round_length")]

    Clock.schedule_once(lambda dt: (
        setattr(sm, "current", "guess_screen"),
        guess_screen.prepare_game(top_tracks)
    ))