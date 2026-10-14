from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from network.client import NetworkClient

from .carrefour_widget import CarrefourWidget
from .control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Simulation Carrefour - SAE (Client)")
        self.resize(900, 620)

        self.carrefour_widget = CarrefourWidget()
        self.control_panel = ControlPanel()

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.carrefour_widget, stretch=3)
        layout.addWidget(self.control_panel, stretch=1)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- Connexion au serveur (adresse lue dans settings.json) ---
        net = settings.get("network", {})
        self.client = NetworkClient(
            net.get("host", "127.0.0.1"),
            net.get("port", 5000),
            net.get("reconnect_delay_s", 2),
        )
        self.client.start()

        # --- Boutons -> commandes envoyees au serveur ---
        self.control_panel.emergency_requested.connect(self.on_emergency)
        self.control_panel.clear_requested.connect(self.on_clear_emergency)

        # --- Toutes les 30 ms : lire le dernier etat recu ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30)

    def on_emergency(self, voie):
        # Le serveur attend une voie qui existe dans Carrefour.VOIES
        self.client.send_command("trigger_emergency", voie)

    def on_clear_emergency(self):
        self.client.send_command("clear_emergency")

    def refresh(self):
        self.control_panel.set_connected(self.client.connected, self.client.last_error)

        state = self.client.consume_latest_state()
        if state is None:
            return

        # Dessin du carrefour
        self.carrefour_widget.set_state(state)

        # Urgence en cours : le serveur envoie la voie (ou None)
        self.control_panel.set_emergency(state.get("urgence"))

        # Trafic : le serveur envoie le nombre de vehicules par voie
        densite = state.get("densite", {})
        if densite:
            texte = "Trafic: "
            for voie, nombre in densite.items():
                texte = texte + voie + " " + str(nombre) + "  "
            self.control_panel.set_traffic(texte.strip())

    def closeEvent(self, event):
        self.client.stop()
        super().closeEvent(event)