from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from threading import Thread

from game_logic import play
from services.spotify import validate_spotify_token, authenticate_spotify

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        label = Label(text="Loading...")

        self.add_widget(label)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")

        label = Label(text="main")
        self.layout.add_widget(label)

        self.play_button = Button(
            text="PLAY",
            font_size=14,
            on_press=lambda _: Thread(target=play, daemon=True).start(),
            disabled=True
        )
        self.layout.add_widget(self.play_button)

        self.spotify_button = Button(
            text="SPOTIFY",
            font_size=14,
            on_press=lambda _: Thread(target=authenticate_spotify, daemon=True).start(),
        )
        self.layout.add_widget(self.spotify_button)

        self.add_widget(self.layout)

        Clock.schedule_once(lambda dt: Thread(target=self.validate_spotify, daemon=True).start(), 0)

    
    def validate_spotify(self):
        sp = validate_spotify_token()

        if sp is not None:
            Clock.schedule_once(lambda dt: setattr(self.play_button, "disabled", False), 0)
            Clock.schedule_once(lambda dt: self.layout.remove_widget(self.spotify_button), 0)
            return
        
        Clock.schedule_once(lambda dt: Thread(target=self.validate_spotify, daemon=True).start(), 5)