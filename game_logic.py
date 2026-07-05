from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import AsyncImage
from kivy.loader import Loader
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar

import logging
import random

from services.lastfm import get_top_tracks, verify_user
from services.spotify import play_song, PlayResult
from matching.aliases import TrackAnswerAliases
from matching.matching import analyze_guess
from utils.utils import get_app, get_settings
from utils.ui_utils import show_error, ColoredProgressBar

logger = logging.getLogger(__name__)

class GuessScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.progress_event = None

        self.ready = False

        layout = BoxLayout(orientation="vertical")

        # Top bar

        top_bar = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=140,
            padding=(30, 10, 30, 10),
        )

        self.round_label = Label(
            text="Loading...",
            font_size=45,
            halign="left",
        )

        top_bar.add_widget(self.round_label)

        self.progressbar = ColoredProgressBar(
            max=60,
            value=0,
            size_hint_y=None,
            height=20
        )

        top_bar.add_widget(self.progressbar)

        layout.add_widget(top_bar)

        # Ans bar

        ans_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=0.35
            )

        self.cover_image = AsyncImage(
            source="assets/unknown_cover.png",
            allow_stretch=True,
            keep_ratio=True
        )
        ans_layout.add_widget(self.cover_image)

        self.label = Label(
            markup=True,
            text_size=(self.width, None),
            size_hint_y=None,
            height=120,
            halign="center",
            valign="middle",
        )
        self.label.bind(width=lambda *args: setattr(self.label, "text_size", (self.label.width, None)))
        ans_layout.add_widget(self.label)

        layout.add_widget(ans_layout)

        # Input label

        input_layout = BoxLayout(orientation="vertical")

        self.input_bar = TextInput(
            multiline=False,
            on_text_validate=self.on_text_enter,
            size_hint_y=None,
            height=60
        )
        input_layout.add_widget(self.input_bar)

        input_layout.add_widget(Widget()) # spacer
        
        layout.add_widget(input_layout)

        self.add_widget(layout)

        ### TODO: Not really happy with this layout ###

    def progressbar_tick(self, max_value, end_function=None):
        self.progressbar.value += 0.025

        if self.progressbar.value >= max_value:
            if self.progress_event:
                self.progress_event.cancel()
                self.progress_event = None

            if end_function:
                end_function()

            return False
    def start_song_timer(self):
        if self.progress_event:
            self.progress_event.cancel()

        self.progressbar.max = 60
        self.progressbar.value = 0
        self.progressbar.set_blue()

        self.progress_event = Clock.schedule_interval(
            lambda dt: self.progressbar_tick(60, self.skip),
            0.025
        )
    
    def start_prepare_round_timer(self, override_function=None):
        if self.progress_event:
            self.progress_event.cancel()

        self.progressbar.max = 5
        self.progressbar.value = 0
        self.progressbar.set_yellow()

        if override_function is None:
            self.progress_event = Clock.schedule_interval(
                lambda dt: self.progressbar_tick(5, self.prepare_round),
                0.025
            )
        else:
            self.progress_event = Clock.schedule_interval(
                lambda dt: self.progressbar_tick(5, lambda: override_function()),
                0.025
            )

    def start_guessing(self):
        self.answer_aliases = TrackAnswerAliases(self.lastfm_track, self.spotify_track)

        self.title_guessed = False
        self.artist_guessed = False

        self.update_display()
        self.start_song_timer()

        self.cover_image.source = "assets/unknown_cover.png"

        # Preload cover image
        Loader.image(self.spotify_track.image_url)

        self.input_bar.disabled = False
        if get_settings().get("input_autofocus"):
            self.input_bar.focus = True

        self.ready = True
    
    def skip(self):
        self.title_guessed = True
        self.artist_guessed = True
        self.finish()

    def on_text_enter(self, instance):
        user_input = instance.text.strip()
        instance.text = ""

        if not self.ready:
            return

        if user_input == "skip":
            self.skip()
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
            if get_settings().get("input_autofocus"):
                Clock.schedule_once(lambda dt: setattr(self.input_bar, "focus", True), 0)

    def update_display(self):
        title = self.lastfm_track.name if self.title_guessed else "XXXX"
        artist = self.lastfm_track.artist if self.artist_guessed else "XXXX"

        self.label.text = f"{title} [color=888888]by[/color] {artist}"
    
    def finish(self):
        self.ready = False

        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None

        self.update_display()

        self.input_bar.disabled = True

        self.cover_image.source = self.spotify_track.image_url

        self.current_track_id += 1
        if self.current_track_id > len(self.tracks)-1:
            self.start_prepare_round_timer(override_function=lambda: setattr(get_app().sm, "current", "home_screen"))
            return
        ### TODO: scoring###

        self.start_prepare_round_timer()
    
    def prepare_round(self):
        self.round_label.text = (
            f"Round {self.current_track_id + 1} / {len(self.tracks)}"
        )
        
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
            self.lastfm_track = track
            self.spotify_track = spotify_data
            
            self.start_guessing()

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
        return

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