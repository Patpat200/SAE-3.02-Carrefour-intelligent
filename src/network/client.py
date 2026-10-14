import socket
import threading

from .protocol import decode_messages, encode_message


class NetworkClient:
    def __init__(self, host, port, reconnect_delay=2):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay

        self.socket = None
        self.running = False
        self.connected = False
        self.last_error = ""

        self.latest_state = None
        self.lock = threading.Lock()
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.close_socket()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=1)

    def send_command(self, action, road=None, value=None):
        sock = self.socket
        if not self.connected or sock is None:
            return False

        message = {"type": "command", "action": action}
        if road is not None:
            message["road"] = road
        if value is not None:
            message["value"] = value

        try:
            sock.sendall(encode_message(message))
            return True
        except OSError as error:
            self.last_error = str(error)
            self.close_socket()
            return False

    def consume_latest_state(self):
        with self.lock:
            state = self.latest_state
            self.latest_state = None
        return state

    def run(self):
        while self.running:
            if not self.connected:
                self.connect()
                if not self.connected:
                    self.stop_event.wait(self.reconnect_delay)
                    continue

            try:
                self.receive_loop()
            except OSError as error:
                self.last_error = str(error)
            except ValueError:
                self.last_error = "Le serveur a envoyé un message JSON invalide"
            self.close_socket()
            self.stop_event.wait(self.reconnect_delay)

    def connect(self):
        try:
            sock = socket.create_connection((self.host, self.port), timeout=3)
            if not self.running:
                sock.close()
                return
            sock.settimeout(1.0)
            self.socket = sock
            self.connected = True
            self.last_error = ""
        except OSError as error:
            self.connected = False
            self.last_error = str(error)

    def receive_loop(self):
        buffer = b""
        sock = self.socket
        while self.running and self.connected and self.socket is not None:
            try:
                data = sock.recv(4096)
            except socket.timeout:
                continue

            if not data:
                self.last_error = "Connexion fermée par le serveur"
                break

            buffer = buffer + data
            messages, buffer = decode_messages(buffer)

            for message in messages:
                if not isinstance(message, dict):
                    raise ValueError("Message invalide")
                if message.get("type") == "state":
                    state = message.get("payload")
                    if not isinstance(state, dict):
                        raise ValueError("État invalide")
                    with self.lock:
                        self.latest_state = state
                elif message.get("type") == "error":
                    self.last_error = message.get("message", "Erreur serveur")

    def close_socket(self):
        self.connected = False
        sock = self.socket
        self.socket = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
