from kivy.uix.screenmanager import Screen, NoTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window

import logging
from threading import Thread

from services.spotify import validate_spotify_token, authenticate_spotify
from utils.utils import get_app, get_settings, handle_spotify_authentication_button

logger = logging.getLogger(__name__)

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        label = Label(text="Loading...")

        self.add_widget(label)

class ErrorScreen(Screen):
    def __init__(self, error_text, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical")

        self.label = Label(
            text=error_text,
            size_hint_y=1,
            text_size=(Window.width * 0.95, None),
            halign="left",
            valign="top",
        )

        layout.add_widget(self.label)

        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=60
        )

        close_btn.bind(on_release=lambda _: self.close_screen())

        layout.add_widget(close_btn)

        self.add_widget(layout)

    def close_screen(self):
        Clock.schedule_once(lambda dt: setattr(get_app().sm, "current", "home_screen"))
    
    def set_error(self, text):
        self.label.text = text

def show_error(error_text, notify_support_prompt=False):
    app = get_app()

    old_sm_transition = app.sm.transition
    app.sm.transition = NoTransition()

    message = str(error_text)

    if notify_support_prompt:
        message = (
            "An unexpected error occurred.\n\n"
            "If this keeps happening, check logs or contact support.\n\n"
            f"Reason:\n{message}"
        )

    app.error_screen.set_error(message)

    def switch_screen(_):
        setattr(app.sm, "current", "error_screen")
        app.sm.transition = old_sm_transition

    Clock.schedule_once(switch_screen)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")

        label = Label(text="main")
        self.layout.add_widget(label)

        from game_logic import play

        self.play_button = Button(
            text="PLAY",
            font_size=14,
            on_press=lambda _: Thread(target=play, daemon=True).start(),
            disabled=True
        )
        self.layout.add_widget(self.play_button)

        self.settings_button = Button(
            text="Settings",
            font_size=14,
            on_press=lambda _: setattr(get_app().sm, "current", "settings_screen"),
        )
        self.layout.add_widget(self.settings_button)

        self.add_widget(self.layout)

        Clock.schedule_once(lambda dt: Thread(target=self.validate_spotify, daemon=True).start(), 0)

    
    def validate_spotify(self):
        sp = validate_spotify_token()

        if sp is not None:
            Clock.schedule_once(lambda dt: setattr(self.play_button, "disabled", False), 0)
            return
        
        Clock.schedule_once(lambda dt: Thread(target=self.validate_spotify, daemon=True).start(), 1)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.inputs = {}
        
        #region main view
        root = BoxLayout(orientation='vertical')

        top_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=10,
            padding=10
        )

        left = Label(
            text="Settings",
            size_hint_x=0.85,
            font_size=24
        )

        right = Button(
            text="Save",
            size_hint_x=0.15
        )
        right.bind(on_press=lambda instance: Thread(target=self.save_and_quit(instance), daemon=True).start())

        top_bar.add_widget(left)
        top_bar.add_widget(right)

        root.add_widget(top_bar)

        self.layout = GridLayout(
            cols=1,
            spacing=10,
            padding=10,
            size_hint_y=None
        )
        self.layout.bind(
            minimum_height=self.layout.setter('height')
        )

        #endregion
        #region settings

        self.add_group_label("General")
        self.add_slider_setting("Round length", 3, 25, 1, "round_length")

        self.add_group_label("Spotify")
        self.add_button("Spotify connection", "Connect" if not validate_spotify_token() != None else "Disconnect", on_press=lambda button: handle_spotify_authentication_button(validate_spotify_token(), button))
        
        self.add_group_label("Last.fm")
        self.add_text_setting("Username", "lastfm_username")
        self.add_text_setting("Max tracks pulled", "lastfm_limit", input_filter="int")
        self.add_choice_setting("Pull period", [("All time", "overall"), ("7 Days", "7day"), ("1 Month", "1month"), ("3 Months", "3month"), ("6 Months", "6month"), ("12 Months", "12month")], "lastfm_period")
        
        #endregion

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.layout)

        root.add_widget(scroll_view)

        self.add_widget(root)

    #region helpers

    def get_default_value(self, key):
        return get_settings().get(key)

    def add_group_label(self, text):
        self.layout.add_widget(
            Label(
                text=text,
                size_hint_y=None,
                height=40,
                font_size=18
            )
        )

    def add_toggle_setting(self, text, key):
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50
        )

        label = Label(text=text, halign='left')
        toggle = Switch(active=self.get_default_value(key))

        row.add_widget(label)
        row.add_widget(toggle)

        self.inputs[key] = toggle

        self.layout.add_widget(row)
    
    def add_button(self, label_text, button_text, on_press):
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50
        )

        label = Label(text=label_text)


        button = Button(
            text=button_text,
            on_press=on_press
        )

        row.add_widget(label)
        row.add_widget(button)

        self.layout.add_widget(row)

    def add_choice_setting(self, text, values: list[tuple[str, str]], key):
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50
        )

        label = Label(text=text)

        values_map = dict(values)

        display, values = [list(a) for a in zip(*values)]
        default_value = display[values.index(self.get_default_value(key))]

        spinner = Spinner(
            text=default_value,
            values=display
        )

        spinner._values_map = values_map

        row.add_widget(label)
        row.add_widget(spinner)

        self.inputs[key] = spinner

        self.layout.add_widget(row)

    def add_slider_setting(self, text, min_val, max_val, step, key):
        row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=90
        )

        default = self.get_default_value(key)

        label = Label(
            text=f"{text}: {default}",
            size_hint_y=None,
            height=30
        )

        slider = Slider(
            min=min_val,
            max=max_val,
            step=step,
            value=default
        )

        def update_label(instance, value):
            label.text = f"{text}: {value}"

        slider.bind(value=update_label)

        row.add_widget(label)
        row.add_widget(slider)

        self.inputs[key] = slider

        self.layout.add_widget(row)

    def add_text_setting(self, text, key, input_filter=None):
        row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=80
        )

        label = Label(
            text=text,
            size_hint_y=None,
            height=30
        )

        input_box = TextInput(
            text= (self.get_default_value(key) if input_filter == None else str(self.get_default_value(key))),
            multiline=False,
            size_hint_y=None,
            input_filter=input_filter,
            height=40
        )

        row.add_widget(label)
        row.add_widget(input_box)

        self.inputs[key] = input_box

        self.layout.add_widget(row)

    def save_and_quit(self, instance):
        settings = get_settings()

        for key, widget in self.inputs.items():
            if isinstance(widget, TextInput):
                value = widget.text

                if widget.input_filter == "int":
                    value = int(value)
                
            elif isinstance(widget, Slider):
                value = widget.value
            
            elif isinstance(widget, Switch):
                value = widget.active
            
            elif isinstance(widget, Spinner):
                value = widget.text
                value = widget._values_map[value]
            
            else:
                logger.warning("Widget in settings with not a known type")
                continue
                
            # Skip unchanged fields
            if value == settings.get(key):
                continue
    
            logger.debug(f"Saving \"{key}\" as \"{value}\"")
            settings.set(key, value)
        
        Clock.schedule_once(lambda dt: setattr(get_app().sm, "current", "home_screen"))

    #endregion