import random
import socket
import threading
import time

from core.carrefour import Carrefour
from utils.logger import EventLogger
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

        if feux_settings is None:
            feux_settings = {}

        # les durées du fichier de config sont en secondes, le carrefour compte en ticks
        tick_duration = max(self.tick_s, 0.001)
        feux_en_ticks = {}
        for nom in ["duree_vert_s", "duree_orange_s", "duree_rouge_s"]:
            nb_ticks = round(feux_settings.get(nom, 0) / tick_duration)
            if nb_ticks < 1:
                nb_ticks = 1
            feux_en_ticks[nom] = nb_ticks

        self.carrefour = Carrefour(feux_en_ticks)
        self.logger = EventLogger(log_path)
        self.clients = []
        self.running = False
        self.server_socket = None

        self.carrefour_lock = threading.Lock()
        self.clients_lock = threading.Lock()
        self.threads = []

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)

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

        self.clients_lock.acquire()
        clients = list(self.clients)
        self.clients = []
        self.clients_lock.release()

        for client in clients:
            try:
                client.close()
            except OSError:
                pass

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)

    def retirer_client(self, client_socket):
        self.clients_lock.acquire()
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        self.clients_lock.release()
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

            client_socket.settimeout(1.0)
            self.clients_lock.acquire()
            self.clients.append(client_socket)
            self.clients_lock.release()

            print("Client connecté:", address)
            handler = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address),
                daemon=True,
            )
            handler.start()
            self.threads.append(handler)

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
        except OSError:
            pass

        self.retirer_client(client_socket)
        print("Client déconnecté:", address)

    def handle_message(self, client_socket, message):
        if message.get("type") != "command":
            self.send_error(client_socket, "Message invalide")
            return

        action = message.get("action")

        self.carrefour_lock.acquire()
        if action == "trigger_emergency":
            voie = message.get("road")
            if voie in Carrefour.VOIES:
                self.carrefour.declencher_urgence(voie)
                self.logger.log("urgence", voie)
            else:
                self.send_error(client_socket, "Voie inconnue")
        elif action == "clear_emergency":
            self.carrefour.fin_urgence()
            self.logger.log("fin_urgence")
        else:
            self.send_error(client_socket, "Commande inconnue")
        self.carrefour_lock.release()

    def simulation_loop(self):
        last_tick = time.monotonic()
        last_vehicle_tick = time.monotonic()
        last_spawn_tick = time.monotonic()
        last_broadcast = time.monotonic()

        while self.running:
            now = time.monotonic()

            self.carrefour_lock.acquire()
            if now - last_tick >= self.tick_s:
                self.carrefour.tick()
                last_tick = now

            if now - last_vehicle_tick >= self.vehicle_tick_s:
                self.carrefour.avancer_vehicules()
                last_vehicle_tick = now

            if now - last_spawn_tick >= self.spawn_tick_s:
                voie = random.choice(Carrefour.VOIES)
                self.carrefour.ajouter_vehicule(voie)
                last_spawn_tick = now

            state = None
            if now - last_broadcast >= self.vehicle_tick_s:
                state = self.carrefour.get_state()
                last_broadcast = now
            self.carrefour_lock.release()

            if state is not None:
                self.broadcast_state(state)

            time.sleep(0.01)

    def broadcast_state(self, state):
        payload = encode_message({"type": "state", "payload": state})

        self.clients_lock.acquire()
        clients = list(self.clients)
        self.clients_lock.release()

        for client in clients:
            try:
                client.sendall(payload)
            except OSError:
                self.retirer_client(client)

    def send_error(self, client_socket, message):
        try:
            client_socket.sendall(encode_message({"type": "error", "message": message}))
        except OSError:
            pass
