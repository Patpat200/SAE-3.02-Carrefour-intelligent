import socket
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path

from src.network.client import NetworkClient
from src.network.server import SimulationServer


class ClientServerTests(unittest.TestCase):
    def wait_state(self, client, condition):
        end = time.monotonic() + 3
        while time.monotonic() < end:
            state = client.consume_latest_state()
            if state is not None and condition(state):
                return state
            time.sleep(0.01)
        self.fail("État attendu non reçu : " + client.last_error)

    def test_four_emergencies_and_sqlite_logging(self):
        with tempfile.TemporaryDirectory() as dossier:
            server = SimulationServer("127.0.0.1", 0, spawn_tick_ms=100000,
                                      log_path=str(Path(dossier) / "events.sqlite3"))
            client = None
            try:
                server.start()
                port = server.server_socket.getsockname()[1]
                client = NetworkClient("127.0.0.1", port, reconnect_delay=0.1)
                client.start()
                state = self.wait_state(client, lambda s: len(s.get("feux", [])) == 4)
                self.assertIsNone(state["urgence"])
                for road in ["Nord", "Sud", "Est", "Ouest"]:
                    self.assertTrue(client.send_command("trigger_emergency", road=road))
                    state = self.wait_state(client, lambda s: s.get("urgence") == road)
                    self.assertTrue(any(v["urgence"] and v["voie"] == road for v in state["vehicules"]))
                    self.assertTrue(client.send_command("clear_emergency"))
                    self.wait_state(client, lambda s: s.get("urgence") is None)
                events = server.logger.get_events()
                self.assertEqual(sum(e["type"] == "urgence" for e in events), 4)
                self.assertEqual(sum(e["type"] == "fin_urgence" for e in events), 4)
            finally:
                if client is not None:
                    client.stop()
                server.stop()

    def test_rejet_json_et_panne_sqlite(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier) / "events.sqlite3"
            server = SimulationServer("127.0.0.1", 0, log_path=base)
            server.start()
            self.addCleanup(server.stop)
            port = server.server_socket.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=2) as socket_invalide:
                socket_invalide.sendall(b"{invalide}\n")
                donnees = b""
                while morceau := socket_invalide.recv(4096):
                    donnees += morceau
            self.assertIn(b"JSON invalide", donnees)
            with server.clients_lock:
                self.assertFalse(server.clients)

            with closing(sqlite3.connect(base)) as connexion:
                connexion.execute("DROP TABLE events")
                connexion.commit()
            client = NetworkClient("127.0.0.1", port)
            client.start()
            self.addCleanup(client.stop)
            self.wait_state(client, lambda etat: client.connected)
            self.assertTrue(client.send_command("trigger_emergency", road="Nord"))
            self.wait_state(client, lambda etat: etat["urgence"] == "Nord")
            self.assertTrue(client.send_command("clear_emergency"))
            self.wait_state(client, lambda etat: etat["urgence"] is None)
            client.stop()
            server.stop()

    def test_reponses_identifiees_et_reglages_trafic(self):
        with tempfile.TemporaryDirectory() as dossier:
            server = SimulationServer("127.0.0.1", 0, log_path=Path(dossier) / "events.sqlite3")
            server.start()
            port = server.server_socket.getsockname()[1]
            client = NetworkClient("127.0.0.1", port)
            client.start()
            try:
                self.wait_state(client, lambda etat: client.connected)
                self.assertTrue(client.send_command("set_strategy", value="adaptatif", request_id="s1"))
                self.assertTrue(client.send_command("set_rush_hour", value=True, request_id="s2"))
                self.assertTrue(client.send_command("trigger_emergency", road="Inconnue", request_id="s3"))
                self.wait_state(client, lambda etat: etat["strategie"] == "adaptatif"
                                and etat["trafic"]["heure_de_pointe"])
                reponses = {}
                limite = time.monotonic() + 2
                while len(reponses) < 3 and time.monotonic() < limite:
                    for reponse in client.consume_results():
                        reponses[reponse["request_id"]] = reponse["ok"]
                    time.sleep(0.01)
                self.assertEqual(reponses, {"s1": True, "s2": True, "s3": False})
            finally:
                client.stop()
                server.stop()


if __name__ == "__main__":
    unittest.main()
