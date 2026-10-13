from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from .carrefour_widget import CarrefourWidget
from .control_panel import ControlPanel


class MainWindow(QMainWindow):
    command_requested = pyqtSignal(str, dict)

    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Simulation Carrefour - Colmar")
        options = settings.get("interface", {})
        self.resize(options.get("largeur", 960), options.get("hauteur", 700))
        self.connected = False

        self.carrefour_widget = CarrefourWidget()
        self.control_panel = ControlPanel(
            self.trigger_emergency, self.clear_emergency,
            self.set_rush_hour, self.set_strategy,
        )

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.carrefour_widget, stretch=3)
        layout.addWidget(self.control_panel, stretch=1)
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.set_connection(False)

    def afficher_etat(self, state):
        self.carrefour_widget.set_state(state)
        self.control_panel.set_density(state.get("densite", {}))
        self.control_panel.set_emergency(state.get("urgence"))
        self.control_panel.set_trafic(state.get("trafic", {}))
        self.control_panel.set_strategie(state.get("strategie", "fixe"))

    def set_connection(self, connected, error_message=""):
        self.connected = connected
        self.control_panel.set_status(connected, error_message)
        if connected:
            self.statusBar().showMessage("Connecté au serveur")
        else:
            self.statusBar().showMessage("Serveur non connecté - affichage non actualisé")

    def trigger_emergency(self, road):
        if self.connected:
            self.command_requested.emit("trigger_emergency", {"road": road})

    def clear_emergency(self):
        if self.connected:
            self.command_requested.emit("clear_emergency", {})

    def set_rush_hour(self, actif):
        if self.connected:
            self.command_requested.emit("set_rush_hour", {"value": actif})

    def set_strategy(self, strategie):
        if self.connected:
            self.command_requested.emit("set_strategy", {"value": strategie})

    def closeEvent(self, event):
        self.carrefour_widget.repaint_timer.stop()
        super().closeEvent(event)
