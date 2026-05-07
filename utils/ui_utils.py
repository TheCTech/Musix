from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from threading import Thread

from game_logic import play

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        label = Label(text="Loading...")

        self.add_widget(label)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical")

        label = Label(text="main")
        layout.add_widget(label)

        button = Button(
            text="PLAY",
            font_size=14,
            on_press=lambda _: Thread(target=play, daemon=True).start()
        )
        layout.add_widget(button)

        self.add_widget(layout)