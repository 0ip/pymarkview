import io
import json

from pathlib import Path


class Settings:
    FILE = "settings.json"

    DEFAULTS = {
        "font_family": "Consolas",
        "font_size": 12,
        "tab_width": 2,
        "word_wrap": True,
        "show_menu": True,
        "md_parser": "markdown2",
        "mathjax": True
    }

    def __init__(self):
        self.__load_settings()

    def __getattr__(self, key: str) -> str:
        return self.DEFAULTS.get(key, None)

    def get(self, key: str) -> str:
        return self.DEFAULTS.get(key, None)

    def set(self, key: str, value) -> None:
        self.DEFAULTS[key] = value
        self.__save_settings()

    def __load_settings(self) -> None:
        if not Path(self.FILE).exists():
            self.__save_settings()
            return

        with io.open(self.FILE, "r", encoding="utf-8") as f:
            try:
                user_settings = json.load(f)
            except json.decoder.JSONDecodeError:
                raise SettingsError("Cannot read settings!")

            for key, value in user_settings.items():
                if key in self.DEFAULTS:
                    self.DEFAULTS[key] = value
                else:
                    print("Found unknown setting '{key}'. Skipping.".format(key=key))

            user_settings_stale = False
            for key, value in self.DEFAULTS.items():
                if key not in user_settings:
                    print("Adding new setting '{key}'.".format(key=key))
                    user_settings_stale = True

            if user_settings_stale:
                self.__save_settings()

    def __save_settings(self) -> None:
        with io.open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(self.DEFAULTS, f, indent=4, sort_keys=True)


class SettingsError(Exception):

    def __init__(self, message):
        super().__init__(message)
