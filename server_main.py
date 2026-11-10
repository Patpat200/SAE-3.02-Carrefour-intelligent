"""Lancement du serveur avec python server_main.py."""

import sqlite3
import time

from src.network.server import SimulationServer
from src.utils.config_loader import load_settings


def main():
    try:
        settings = load_settings(use_local=False)
        options = settings.get("serveur", {})
        server = SimulationServer(
            options.get("host", "0.0.0.0"),
            options.get("port", 5000),
            tick_ms=options.get("tick_ms", 500),
            vehicle_tick_ms=options.get("vehicle_tick_ms", 30),
            spawn_tick_ms=options.get("spawn_tick_ms", 1200),
            feux_settings=settings.get("feux"),
            log_path=options.get("log_path", "logs/events.sqlite3"),
        )
        server.start()
    except (OSError, ValueError, OverflowError, sqlite3.Error) as erreur:
        raise SystemExit(f"Démarrage du serveur impossible : {erreur}") from erreur

    print("Serveur démarré. Ctrl+C pour arrêter.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arrêt du serveur.")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
