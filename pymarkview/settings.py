import io
import json

from pathlib import Path


class Settings:
    FILE = "settings.json"

    settings = {
        "tab_width": 2,
        "word_wrap": True
    }

    def __init__(self):
        self.__load_settings()

    def __getattr__(self, key):
        return self.settings.get(key, None)

    def get(self, key):
        return self.settings.get(key, None)

    def set(self, key, value):
        self.settings[key] = value
        self.__save_settings()

    def __load_settings(self):
        if not Path(self.FILE).exists():
            self.__save_settings()
            return

        with io.open(self.FILE, "r", encoding="utf-8") as f:
            try:
                user_settings = json.load(f)
            except json.decoder.JSONDecodeError:
                raise SettingsError("Cannot read settings!")

            for key, value in user_settings.items():
                if key in self.settings.keys():
                    self.settings[key] = value
                else:
                    print("Found unknown setting '{key}'. Skipping.".format(key=key))

    def __save_settings(self):
        with io.open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f)


class SettingsError(Exception):
    def __init__(self, message):
        super().__init__(message)