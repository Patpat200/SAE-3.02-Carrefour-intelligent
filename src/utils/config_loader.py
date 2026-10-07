import json
import os


DOSSIER_PROJET = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SETTINGS_PATH = os.path.join(DOSSIER_PROJET, "config", "settings.json")


def load_settings(settings_path=None):
    if settings_path is None:
        settings_path = DEFAULT_SETTINGS_PATH
    config_file = open(settings_path, "r", encoding="utf-8")
    settings = json.load(config_file)
    config_file.close()
    return settings
