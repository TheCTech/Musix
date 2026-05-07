from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        label = Label(text="Loading...")

        self.add_widget(label)