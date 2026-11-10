import json
from pathlib import Path


DOSSIER_PROJET = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = DOSSIER_PROJET / "config" / "settings.json"
LOCAL_SETTINGS_PATH = DOSSIER_PROJET / "config" / "local_settings.json"


def load_settings(settings_path=None, use_local=True):
    chemin = Path(settings_path) if settings_path is not None else DEFAULT_SETTINGS_PATH
    with chemin.open(encoding="utf-8") as fichier:
        settings = json.load(fichier)

    if settings_path is None and use_local and LOCAL_SETTINGS_PATH.exists():
        try:
            with LOCAL_SETTINGS_PATH.open(encoding="utf-8") as fichier:
                local = json.load(fichier)
        except (OSError, ValueError) as erreur:
            print("Préférences locales ignorées :", erreur)
        else:
            if isinstance(local, dict):
                for section in ("interface", "network"):
                    if isinstance(local.get(section), dict):
                        settings.setdefault(section, {}).update(local[section])
    return settings


def save_settings(settings, settings_path=None):
    chemin = Path(settings_path) if settings_path is not None else LOCAL_SETTINGS_PATH
    if settings_path is None:
        settings = {section: settings[section] for section in ("interface", "network")
                    if section in settings}
    with chemin.open("w", encoding="utf-8") as fichier:
        json.dump(settings, fichier, ensure_ascii=False, indent=4)
        fichier.write("\n")
