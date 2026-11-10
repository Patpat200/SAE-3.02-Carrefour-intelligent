import random
import sqlite3
import socket
import threading
import time

from src.core.carrefour import Carrefour
from src.utils.logger import EventLogger
from .protocol import decode_messages, encode_message


class SimulationServer:
    def __init__(
        self,
        host,
        port,
        tick_ms=500,
        vehicle_tick_ms=30,
        spawn_tick_ms=1200,
        feux_settings=None,
        log_path="logs/events.sqlite3",
    ):
        self.host = host
        self.port = port
        self.tick_s = tick_ms / 1000
        self.vehicle_tick_s = vehicle_tick_ms / 1000
        self.spawn_tick_s = spawn_tick_ms / 1000
        if min(self.tick_s, self.vehicle_tick_s, self.spawn_tick_s) <= 0:
            raise ValueError("Les intervalles de simulation doivent être positifs")
        self.debut_heure_de_pointe = None

        if feux_settings is None:
            feux_settings = {}

        # les durées du fichier de config sont en secondes, le carrefour compte en ticks
        feux_en_ticks = {}
        for nom, defaut in (("duree_vert_s", 5), ("duree_orange_s", 2)):
            duree = feux_settings.get(nom, defaut)
            if duree <= 0:
                raise ValueError("Les durées des feux doivent être positives")
            feux_en_ticks[nom] = max(1, round(duree / self.tick_s))

        self.carrefour = Carrefour(feux_en_ticks)
        self.logger = EventLogger(log_path)
        self.clients = {}
        self.running = False
        self.server_socket = None

        self.carrefour_lock = threading.Lock()
        self.clients_lock = threading.Lock()
        self.threads = []

    def start(self):
        if self.running:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen()
            sock.settimeout(0.25)
        except (OSError, OverflowError):
            sock.close()
            raise
        self.server_socket = sock
        self.running = True

        print("Serveur en écoute sur " + self.host + ":" + str(self.port))

        accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
        simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)

        accept_thread.start()
        simulation_thread.start()

        self.threads.append(accept_thread)
        self.threads.append(simulation_thread)

    def stop(self):
        self.running = False
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass

        with self.clients_lock:
            clients = list(self.clients)
            self.clients.clear()

        for client in clients:
            try:
                client.close()
            except OSError:
                pass

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)

    def retirer_client(self, client_socket):
        with self.clients_lock:
            self.clients.pop(client_socket, None)
        try:
            client_socket.close()
        except OSError:
            pass

    def accept_loop(self):
        while self.running and self.server_socket is not None:
            try:
                client_socket, address = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_socket.settimeout(0.25)
            with self.clients_lock:
                if not self.running:
                    client_socket.close()
                    break
                self.clients[client_socket] = threading.Lock()

            print("Client connecté:", address)
            handler = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address),
                daemon=True,
            )
            handler.start()


    def handle_client(self, client_socket, address):
        buffer = b""
        try:
            while self.running:
                try:
                    data = client_socket.recv(4096)
                except socket.timeout:
                    continue

                if not data:
                    break

                buffer = buffer + data
                messages, buffer = decode_messages(buffer)
                for message in messages:
                    self.handle_message(client_socket, message)
        except ValueError:
            self.send_error(client_socket, "JSON invalide ou message trop long")
        except OSError:
            pass
        finally:
            self.retirer_client(client_socket)
            print("Client déconnecté:", address)

    def handle_message(self, client_socket, message):
        if not isinstance(message, dict) or message.get("type") != "command":
            self.send_error(client_socket, "Message invalide")
            return

        action = message.get("action")
        identifiant = message.get("request_id")
        if not isinstance(identifiant, str) or len(identifiant) > 64:
            identifiant = None

        try:
            with self.carrefour_lock:
                if action == "trigger_emergency":
                    voie = message.get("road")
                    resultat = self.carrefour.declencher_urgence(
                        voie, message.get("destination"), message.get("vehicle_type", "Secours")
                    )
                    evenement, details = "urgence", voie
                elif action == "clear_emergency":
                    resultat = self.carrefour.fin_urgence()
                    evenement, details = "fin_urgence", resultat
                elif action == "set_strategy":
                    strategie = message.get("value")
                    if strategie not in ("fixe", "adaptatif"):
                        raise ValueError("Stratégie inconnue")
                    self.carrefour.strategie = strategie
                    resultat = "Stratégie " + strategie + " appliquée à la prochaine phase"
                    evenement, details = "strategie", strategie
                elif action == "set_rush_hour":
                    actif = message.get("value")
                    if not isinstance(actif, bool):
                        raise ValueError("L’heure de pointe attend vrai ou faux")
                    if actif and self.debut_heure_de_pointe is None:
                        self.debut_heure_de_pointe = time.monotonic()
                    elif not actif:
                        self.debut_heure_de_pointe = None
                    resultat = "Heure de pointe " + ("activée" if actif else "désactivée")
                    evenement, details = "heure_de_pointe", str(actif)
                else:
                    raise ValueError("Commande inconnue")
        except ValueError as erreur:
            if identifiant is None:
                self.send_error(client_socket, str(erreur))
            else:
                self.send_result(client_socket, identifiant, False, str(erreur))
            return

        # SQLite n’a pas besoin du verrou de la simulation.
        try:
            self.logger.log(evenement, details)
        except sqlite3.Error as erreur:
            print("Journal SQLite indisponible :", erreur)
        if identifiant is not None:
            self.send_result(client_socket, identifiant, True, resultat)

    def lire_trafic(self, maintenant):
        if self.debut_heure_de_pointe is None:
            return {"heure_de_pointe": False, "heure": "", "niveau": 1}, (1, 1, 1, 1)

        # La journée démarre à 7 h et avance de deux minutes par seconde.
        minutes = (420 + int(max(0, maintenant - self.debut_heure_de_pointe) * 2)) % 1440
        heure, minute = divmod(minutes, 60)
        if 7 <= heure < 10:
            niveau, poids = 2.2, (3, 3, 1, 1)
        elif 16 <= heure < 19:
            niveau, poids = 2.2, (1, 1, 3, 3)
        elif heure < 6 or heure >= 22:
            niveau, poids = 0.45, (1, 1, 1, 1)
        else:
            niveau, poids = 1, (1, 1, 1, 1)
        return {
            "heure_de_pointe": True, "heure": f"{heure:02d}:{minute:02d}", "niveau": niveau
        }, poids

    def simulation_loop(self):
        last_tick = time.monotonic()
        last_vehicle_tick = time.monotonic()
        last_spawn_tick = time.monotonic()
        last_broadcast = time.monotonic()

        while self.running:
            now = time.monotonic()

            with self.carrefour_lock:
                if now - last_tick >= self.tick_s:
                    self.carrefour.tick()
                    last_tick = now

                if now - last_vehicle_tick >= self.vehicle_tick_s:
                    self.carrefour.avancer_vehicules()
                    last_vehicle_tick = now

                trafic, poids = self.lire_trafic(now)
                if now - last_spawn_tick >= self.spawn_tick_s / trafic["niveau"]:
                    voie = random.choices(Carrefour.VOIES, weights=poids)[0]
                    self.carrefour.ajouter_vehicule(voie)
                    last_spawn_tick = now

                state = None
                if now - last_broadcast >= self.vehicle_tick_s:
                    state = self.carrefour.get_state()
                    state["trafic"] = trafic
                    state["confirmation_commandes"] = True
                    last_broadcast = now

            if state is not None:
                self.broadcast_state(state)

            time.sleep(0.01)

    def broadcast_state(self, state):
        payload = encode_message({"type": "state", "payload": state})
        with self.clients_lock:
            clients = list(self.clients)
        for client in clients:
            self.send_payload(client, payload)

    def send_error(self, client_socket, message):
        self.send_payload(client_socket, encode_message({"type": "error", "message": message}))

    def send_result(self, client_socket, identifiant, success, message):
        reponse = {"type": "result", "request_id": identifiant, "ok": success, "message": message}
        self.send_payload(client_socket, encode_message(reponse))

    def send_payload(self, client_socket, payload):
        with self.clients_lock:
            verrou = self.clients.get(client_socket)
        if verrou is None:
            return
        try:
            # Les réponses et les états utilisent le même flux TCP.
            with verrou:
                client_socket.sendall(payload)
        except OSError:
            self.retirer_client(client_socket)
