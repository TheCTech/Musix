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
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.progressbar import ProgressBar

import logging
import shutil
from threading import Thread

from services.spotify import validate_spotify_token
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

        self.close_btn = Button(
            size_hint_y=None,
            height=150
        )

        self.prepare_button()

        self.close_btn.bind(on_release=lambda _: self.close_screen())

        layout.add_widget(self.close_btn)

        self.add_widget(layout)
    
    def prepare_button(self, fatal_error=False):
        self.close_btn.text = "Close" if not fatal_error else "Fatal error, please restart the app"
        self.close_btn.disabled = True if fatal_error else False

    def close_screen(self):
        Clock.schedule_once(lambda dt: setattr(get_app().sm, "current", "home_screen"))
    
    def set_error(self, text):
        self.label.text = text

def show_error(error_text, notify_support_prompt=False, fatal_error=False):
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
    if fatal_error:
        logger.error("Fatal error, showing error screen with disabled close button")
        logger.info(f"Error: {error_text}")
        app.error_screen.prepare_button(fatal_error=True)

    def switch_screen(_):
        app.sm.current = "error_screen"
        if fatal_error:
            app.sm.lock()
        app.sm.transition = old_sm_transition

    Clock.schedule_once(switch_screen)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")

        label = Label(
            text="main",
            font_size=45
            )
        self.layout.add_widget(label)

        from game_logic import play

        self.play_button = Button(
            text="PLAY",
            #font_size=14,
            on_press=lambda _: Thread(target=play, daemon=True).start(),
            disabled=True
        )
        self.layout.add_widget(self.play_button)

        self.settings_button = Button(
            text="Settings",
            font_size=45,
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
            height=120,
            spacing=10,
            padding=10
        )

        left = Label(
            text="Settings",
            size_hint_x=0.85,
            font_size=45
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
            spacing=25,
            padding=20,
            size_hint_y=None
        )
        self.layout.bind(
            minimum_height=self.layout.setter('height')
        )

        #endregion
        #region settings

        self.add_group_label("General")
        self.add_slider_setting("Round length", 3, 25, 1, "round_length")
        self.add_toggle_setting("Input autofocus", "input_autofocus")

        self.add_group_label("Spotify")
        self.add_button("Spotify connection", "Connect" if not validate_spotify_token() != None else "Disconnect", on_press=lambda button: handle_spotify_authentication_button(validate_spotify_token(), button))
        
        self.add_group_label("Last.fm")
        self.add_text_setting("Username", "lastfm_username")
        self.add_text_setting("Max tracks pulled", "lastfm_limit", input_filter="int")
        self.add_choice_setting("Pull period", [("All time", "overall"), ("7 Days", "7day"), ("1 Month", "1month"), ("3 Months", "3month"), ("6 Months", "6month"), ("12 Months", "12month")], "lastfm_period")
        
        if get_settings().get("debug_mode"):
            self.add_group_label("Debug")
            self.add_button("Disable debug mode", "Disable", lambda _: (get_settings().set("debug_mode", False), show_error("Debug mode disabled, please restart the app", fatal_error=True)))
            self.add_toggle_setting("Spotify DND mode", "spotify_do_not_disturb_mode")
            self.add_button("Clear cache", "Clear", lambda _: (shutil.rmtree("cache"), show_error("The app needs to restart after cache removal", fatal_error=True)))

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
                size_hint_y=None,\
                height=80,
                font_size=50
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
            height=75
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
            height=75
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
            height=120,
            spacing=10
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

        row.add_widget(Widget(size_hint_y=None, height=8))
        row.add_widget(label)
        row.add_widget(Widget(size_hint_y=None, height=6))
        row.add_widget(slider)

        self.inputs[key] = slider

        self.layout.add_widget(row)

    def add_text_setting(self, text, key, input_filter=None):
        row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=120
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
            height=60
        )

        row.add_widget(label)
        row.add_widget(Widget(size_hint_y=None, height=10))
        row.add_widget(input_box)

        self.inputs[key] = input_box

        self.layout.add_widget(row)

    def save_and_quit(self, instance):
        settings = get_settings()
        debug_mode_activated = False

        for key, widget in self.inputs.items():
            if isinstance(widget, TextInput):
                value = widget.text

                if widget.input_filter == "int":
                    value = int(value)
                
                if key == "lastfm_username" and value == "#DEBUG":
                    settings.set("debug_mode", True)
                    logger.warning("Debug mode activated")
                    debug_mode_activated = True
                    continue
                
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
        

        if debug_mode_activated:
            show_error("Debug mode activated, please restart the app.", fatal_error=True)
            return
        
        Clock.schedule_once(lambda dt: setattr(get_app().sm, "current", "home_screen"))

    #endregion

from kivy.graphics import Color, BorderImage
from kivy.uix.progressbar import ProgressBar


class ColoredProgressBar(ProgressBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bar_source = "assets/progress_blue.png"

        self.canvas.clear() # type: ignore

        with self.canvas: # type: ignore
            Color(1, 1, 1, 1)

            self.bg = BorderImage(
                source="atlas://data/images/defaulttheme/progressbar_background",
                border=(12, 12, 12, 12),
            )

            self.fg = BorderImage(
                source=self.bar_source,
                border=(12, 12, 12, 12),
            )

        self.bind(pos=self.update_canvas,
                  size=self.update_canvas,
                  value=self.update_canvas,
                  max=self.update_canvas)

        self.update_canvas()

    def set_blue(self):
        self.bar_source = "assets/progress_blue.png"
        self.fg.source = self.bar_source

    def set_yellow(self):
        self.bar_source = "assets/progress_yellow.png"
        self.fg.source = self.bar_source

    def update_canvas(self, *args):
        self.bg.pos = (self.x, self.center_y - 12)
        self.bg.size = (self.width, 24)

        width = 0
        if self.max:
            width = self.width * self.value / self.max

        self.fg.pos = (self.x, self.center_y - 12)
        self.fg.size = (width, 24)

        border = min(int(width), 12)
        self.fg.border = (border, border, border, border)