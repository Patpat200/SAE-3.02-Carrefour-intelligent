from PyQt6.QtCore import QTimer, pyqtSignal
from datetime import datetime
import time
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QScrollArea, QWidget

from .carrefour_widget import CarrefourWidget
from .control_panel import ControlPanel
from ..network.client import NetworkClient
from ..utils.config_loader import save_settings
from ..utils.history_export import export_history


class MainWindow(QMainWindow):
    command_requested = pyqtSignal(str, dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.last_state_time = None
        self.manual_disconnect = False
        self.setWindowTitle("Simulation Carrefour - Colmar")
        options = settings.get("interface", {})
        self.resize(options.get("largeur", 960), options.get("hauteur", 700))
        self.connected = False
        self.last_emergency = None
        self.last_strategy = None
        self.last_rush_hour = None

        self.carrefour_widget = CarrefourWidget()
        self.control_panel = ControlPanel(
            self.trigger_emergency, self.clear_emergency,
            self.set_rush_hour, self.set_strategy,
        )
        self.control_panel.decor_checkbox.toggled.connect(self.carrefour_widget.set_decor_visible)
        panneau_scroll = QScrollArea()
        panneau_scroll.setWidgetResizable(True)
        panneau_scroll.setMinimumWidth(350)
        panneau_scroll.setWidget(self.control_panel)

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.carrefour_widget, stretch=3)
        layout.addWidget(panneau_scroll, stretch=1)
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.set_connection(False)
        self.control_panel.set_strategie(None)
        self.control_panel.add_event("Interface ouverte")

        network = settings.get("network", {})
        self.control_panel.host_input.setText(network.get("host", "127.0.0.1"))
        self.control_panel.port_input.setValue(network.get("port", 5000))
        self.control_panel.connect_button.clicked.connect(self.connect_to_server)
        self.control_panel.disconnect_button.clicked.connect(self.disconnect_from_server)
        self.control_panel.export_history_button.clicked.connect(self.save_history)
        self.control_panel.capture_button.clicked.connect(self.save_capture)
        self.client = NetworkClient(
            network.get("host", "127.0.0.1"),
            network.get("port", 5000),
            network.get("reconnect_delay_s", 2),
        )
        self.last_network_error = ""
        self.command_requested.connect(self.envoyer_commande)
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.refresh)
        self.client.start()
        self.network_timer.start(50)

    def envoyer_commande(self, action, params):
        if not self.client.send_command(action, **params):
            self.set_connection(False, self.client.last_error or "Commande non envoyée")

    def refresh(self):
        if self.manual_disconnect:
            self.set_connection(False, "Déconnexion volontaire")
            self.update_data_status()
            return
        self.set_connection(self.client.connected, self.client.last_error)
        state = self.client.consume_latest_state()
        if state is not None:
            self.afficher_etat(state)
        if self.client.last_error and self.client.last_error != self.last_network_error:
            self.control_panel.add_event("Erreur réseau : " + self.client.last_error)
        self.last_network_error = self.client.last_error
        self.update_data_status()

    def update_data_status(self):
        age = None if self.last_state_time is None else time.monotonic() - self.last_state_time
        texte = self.control_panel.set_data_age(age, self.connected)
        stale = age is None or not self.connected or age >= 3
        self.carrefour_widget.set_data_message(texte, stale)

    def connect_to_server(self):
        host = self.control_panel.host_input.text().strip()
        port = self.control_panel.port_input.value()
        if not host or any(c.isspace() for c in host) or "/" in host:
            self.statusBar().showMessage("Renseigne une adresse IP ou un nom de serveur valide")
            return
        self.client.stop()
        self.settings.setdefault("network", {}).update({"host": host, "port": port})
        try:
            save_settings(self.settings)
        except OSError as error:
            self.control_panel.add_event("Adresse non enregistrée : " + str(error))
        self.manual_disconnect = False
        self.last_network_error = ""
        self.last_state_time = None
        self.last_emergency = None
        self.last_strategy = None
        self.last_rush_hour = None
        self.carrefour_widget.set_state({"feux": [], "vehicules": [], "densite": {}})
        self.control_panel.set_density({})
        self.control_panel.set_feux([])
        self.control_panel.set_emergency(None)
        self.control_panel.set_trafic({})
        self.control_panel.set_strategie(None)
        self.control_panel.last_update_label.setText("Aucune donnée reçue")
        self.client = NetworkClient(host, port, self.settings["network"].get("reconnect_delay_s", 2))
        self.set_connection(False, "Connexion en cours…")
        self.control_panel.disconnect_button.setEnabled(True)
        self.control_panel.add_event("Connexion demandée vers " + host + ":" + str(port))
        self.client.start()
        self.update_data_status()

    def disconnect_from_server(self):
        self.manual_disconnect = True
        self.client.stop()
        self.client.consume_latest_state()
        self.control_panel.add_event("Déconnexion volontaire")
        self.control_panel.disconnect_button.setEnabled(False)
        self.set_connection(False, "Déconnexion volontaire")
        self.update_data_status()

    def save_history(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter l'historique", "historique.txt", "Texte (*.txt)")
        if not path:
            return
        entries = [self.control_panel.history_list.item(i).text()
                   for i in range(self.control_panel.history_list.count())]
        try:
            export_history(entries, path)
        except OSError as error:
            QMessageBox.warning(self, "Export impossible", str(error))
        else:
            self.statusBar().showMessage("Historique enregistré dans " + path)

    def save_capture(self):
        path, _ = QFileDialog.getSaveFileName(self, "Capturer le carrefour", "carrefour.png", "Images PNG (*.png)")
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if self.carrefour_widget.grab().save(path, "PNG"):
            self.statusBar().showMessage("Capture enregistrée dans " + path)
        else:
            QMessageBox.warning(self, "Capture impossible", "Impossible d'enregistrer l'image dans ce fichier.")

    def afficher_etat(self, state):
        self.last_state_time = time.monotonic()
        self.carrefour_widget.set_state(state)
        self.control_panel.set_density(state.get("densite", {}))
        self.control_panel.set_feux(state.get("feux", []))
        self.control_panel.set_emergency(state.get("urgence"))
        self.control_panel.set_trafic(state.get("trafic", {}))
        self.control_panel.set_strategie(state.get("strategie"))
        self.control_panel.last_update_label.setText("Dernières données : " + datetime.now().strftime("%H:%M:%S"))
        urgence = state.get("urgence")
        if urgence != self.last_emergency:
            texte = "Urgence signalée : " + urgence if urgence else "Urgence terminée"
            self.control_panel.add_event(texte)
            self.last_emergency = urgence
        strategie = state.get("strategie")
        if strategie is not None and strategie != self.last_strategy:
            self.control_panel.add_event("Stratégie reçue : " + strategie)
            self.last_strategy = strategie
        pointe = state.get("trafic", {}).get("heure_de_pointe")
        if pointe is not None and pointe != self.last_rush_hour:
            self.control_panel.add_event("Heure de pointe " + ("active" if pointe else "inactive"))
            self.last_rush_hour = pointe

    def set_connection(self, connected, error_message=""):
        if connected != self.connected:
            self.control_panel.add_event("Serveur connecté" if connected else "Serveur déconnecté")
        self.connected = connected
        self.control_panel.set_status(connected, error_message)
        if connected:
            texte = "Connecté au serveur"
            if error_message:
                texte += " — " + error_message
            self.statusBar().showMessage(texte)
        else:
            self.statusBar().showMessage(error_message or "Serveur non connecté - affichage non actualisé")

    def trigger_emergency(self, road):
        if self.connected:
            self.control_panel.add_event("Demande d'urgence : " + road)
            self.command_requested.emit("trigger_emergency", {"road": road})

    def clear_emergency(self):
        if self.connected:
            self.control_panel.add_event("Demande de fin d'urgence")
            self.command_requested.emit("clear_emergency", {})

    def set_rush_hour(self, actif):
        if self.connected and self.control_panel.trafic_available:
            self.control_panel.add_event("Demande d'heure de pointe : " + ("activer" if actif else "désactiver"))
            self.command_requested.emit("set_rush_hour", {"value": actif})

    def set_strategy(self, strategie):
        if self.connected and self.control_panel.strategie in ["fixe", "adaptatif"]:
            self.control_panel.add_event("Demande de stratégie : " + strategie)
            self.command_requested.emit("set_strategy", {"value": strategie})

    def closeEvent(self, event):
        self.network_timer.stop()
        self.client.stop()
        self.carrefour_widget.repaint_timer.stop()
        super().closeEvent(event)
