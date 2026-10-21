import copy
import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


class FakeClient:
    def __init__(self, *args):
        self.connected = False
        self.running = False
        self.last_error = ""
        self.state = None
        self.commands = []
        self.send_success = True

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        self.connected = False

    def consume_latest_state(self):
        state = self.state
        self.state = None
        return state

    def send_command(self, action, **params):
        self.commands.append((action, params))
        if not self.send_success:
            self.connected = False
        return self.send_success


def sample_state():
    return {
        "feux": [{"nom": voie, "etat": "ROUGE"} for voie in ["Nord", "Sud", "Est", "Ouest"]],
        "vehicules": [
            {"id": "v1", "voie": "Nord", "position": -100, "longueur": 30, "urgence": False},
            {"id": "v2", "voie": "Est", "position": -120, "longueur": 30, "urgence": True},
        ],
        "densite": {"Nord": 1, "Sud": 0, "Est": 1, "Ouest": 0},
        "urgence": None,
    }


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["tests-interface"])

    def setUp(self):
        patcher = patch("src.ui.main_window.NetworkClient", FakeClient)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.window = MainWindow({"network": {"host": "127.0.0.1", "port": 5000}})
        self.window.network_timer.stop()
        self.addCleanup(self.window.close)
        self.window.client.connected = True
        self.window.client.state = sample_state()
        self.window.refresh()

    def test_vehicle_selection_survives_position_update(self):
        panel = self.window.vehicle_panel
        panel.table.selectRow(0)
        self.assertEqual(self.window.carrefour_widget.selected_vehicle_id, "v1")
        state = sample_state()
        state["vehicules"][0]["position"] = -80
        original = copy.deepcopy(state)
        self.window.afficher_etat(state)
        self.assertEqual(panel.selected_id, "v1")
        self.assertEqual(state, original)

    def test_filters_and_vehicle_departure(self):
        panel = self.window.vehicle_panel
        panel.emergency_filter.setChecked(True)
        self.assertEqual(panel.visible_ids, ["v2"])
        panel.table.selectRow(0)
        self.assertEqual(self.window.carrefour_widget.selected_vehicle_id, "v2")
        panel.road_filter.setCurrentText("Nord")
        self.assertEqual(panel.table.rowCount(), 0)
        self.assertEqual(self.window.carrefour_widget.selected_vehicle_id, "")
        panel.road_filter.setCurrentIndex(0)
        panel.table.selectRow(0)
        self.window.afficher_etat({"feux": [], "vehicules": [], "densite": {}, "urgence": None})
        self.assertEqual(panel.selected_id, "")

    def test_emergency_requires_matching_server_state(self):
        self.window.trigger_emergency("Nord")
        self.assertIsNotNone(self.window.pending_command)
        state = sample_state()
        state["urgence"] = "Est"
        self.window.afficher_etat(state)
        self.assertIsNotNone(self.window.pending_command)
        state["urgence"] = "Nord"
        self.window.afficher_etat(state)
        self.assertIsNone(self.window.pending_command)
        self.assertIn("État observé", self.window.control_panel.command_status_label.text())

    def test_clear_requires_explicit_emergency_field(self):
        self.window.clear_emergency()
        self.window.check_pending_command({})
        self.assertIsNotNone(self.window.pending_command)
        self.window.check_pending_command({"urgence": None})
        self.assertIsNone(self.window.pending_command)

    def test_command_timeout_can_later_be_observed(self):
        self.window.trigger_emergency("Sud")
        self.window.pending_command["time"] = time.monotonic() - 6
        self.window.refresh()
        self.assertIn("non observé", self.window.control_panel.command_status_label.text())
        self.window.check_pending_command({"urgence": "Sud"})
        self.assertIsNone(self.window.pending_command)

    def test_failed_send_and_disconnect(self):
        self.window.client.send_success = False
        self.window.trigger_emergency("Nord")
        self.assertIsNone(self.window.pending_command)
        self.assertEqual(self.window.control_panel.command_status_label.text(), "Demande non envoyée")
        self.window.client.send_success = True
        self.window.client.connected = True
        self.window.refresh()
        self.window.trigger_emergency("Est")
        self.window.disconnect_from_server()
        self.assertIsNone(self.window.pending_command)
        self.assertFalse(self.window.client.running)
        self.assertFalse(any(b.isEnabled() for b in self.window.control_panel.command_buttons))

    def test_stale_data_and_unsupported_commands(self):
        self.window.last_state_time = time.monotonic() - 6
        self.window.refresh()
        self.assertTrue(self.window.carrefour_widget.data_stale)
        self.assertFalse(self.window.control_panel.bouton_pointe.isEnabled())
        self.assertFalse(self.window.control_panel.bouton_strategie.isEnabled())
        self.window.set_rush_hour(True)
        self.window.set_strategy("adaptatif")
        self.assertEqual(self.window.client.commands, [])


if __name__ == "__main__":
    unittest.main()
