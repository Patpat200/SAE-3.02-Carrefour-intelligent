import tempfile
import time
import unittest
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


if __name__ == "__main__":
    unittest.main()
