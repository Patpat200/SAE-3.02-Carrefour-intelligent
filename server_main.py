"""Point d'entree du serveur de simulation du carrefour.

Usage :
    python server_main.py
"""

import os
import sys
import time

# Force Python a chercher les dossiers (network, core, utils) a cote de ce fichier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.network.server import SimulationServer

HOST = "0.0.0.0"   # ecoute sur toutes les interfaces
PORT = 5000

# Durees des feux en secondes (converties en ticks par SimulationServer)
FEUX_SETTINGS = {
    "duree_vert_s": 5,
    "duree_orange_s": 2,
    "duree_rouge_s": 5,
}


def main():
    server = SimulationServer(
        HOST,
        PORT,
        tick_ms=500,
        vehicle_tick_ms=30,
        spawn_tick_ms=1200,
        feux_settings=FEUX_SETTINGS,
        log_path="logs/events.sqlite3",
    )
    server.start()   # lance les threads d'ecoute et de simulation, puis rend la main

    print("Serveur demarre. Ctrl+C pour arreter.")
    try:
        # SimulationServer utilise des threads daemon : le programme
        # principal doit rester en vie, sinon tout s'arrete.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arret du serveur...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()