import socket
import threading
import time

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

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.close_socket()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=1)

    def send_command(self, action, road=None):
        if not self.connected or self.socket is None:
            return False

        message = {"type": "command", "action": action}
        if road is not None:
            message["road"] = road

        try:
            self.socket.sendall(encode_message(message))
            return True
        except OSError as error:
            self.last_error = str(error)
            self.close_socket()
            return False

    def consume_latest_state(self):
        self.lock.acquire()
        state = self.latest_state
        self.latest_state = None
        self.lock.release()
        return state

    def run(self):
        while self.running:
            if not self.connected:
                self.connect()
                if not self.connected:
                    time.sleep(self.reconnect_delay)
                    continue

            try:
                self.receive_loop()
            except OSError as error:
                self.last_error = str(error)
            self.close_socket()

    def connect(self):
        try:
            sock = socket.create_connection((self.host, self.port), timeout=3)
            sock.settimeout(1.0)
            self.socket = sock
            self.connected = True
            self.last_error = ""
        except OSError as error:
            self.connected = False
            self.last_error = str(error)

    def receive_loop(self):
        buffer = b""
        while self.running and self.connected and self.socket is not None:
            try:
                data = self.socket.recv(4096)
            except socket.timeout:
                continue

            if not data:
                self.last_error = "Connexion fermée par le serveur"
                break

            buffer = buffer + data
            messages, buffer = decode_messages(buffer)

            for message in messages:
                if message.get("type") == "state":
                    self.lock.acquire()
                    self.latest_state = message.get("payload")
                    self.lock.release()
                elif message.get("type") == "error":
                    self.last_error = message.get("message", "Erreur serveur")

    def close_socket(self):
        self.connected = False
        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None
