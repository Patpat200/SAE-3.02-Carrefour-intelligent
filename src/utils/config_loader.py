import json
import os


DOSSIER_PROJET = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SETTINGS_PATH = os.path.join(DOSSIER_PROJET, "config", "settings.json")


def load_settings(settings_path=None):
    if settings_path is None:
        settings_path = DEFAULT_SETTINGS_PATH
    with open(settings_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_settings(settings, settings_path=None):
    if settings_path is None:
        settings_path = DEFAULT_SETTINGS_PATH
    with open(settings_path, "w", encoding="utf-8") as config_file:
        json.dump(settings, config_file, ensure_ascii=False, indent=4)
        config_file.write("\n")
