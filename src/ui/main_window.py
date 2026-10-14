from PyQt6.QtCore import pyqtSignal
from datetime import datetime
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QScrollArea, QWidget

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
        panneau_scroll.setMinimumWidth(320)
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

    def afficher_etat(self, state):
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
            self.statusBar().showMessage("Connecté au serveur")
        else:
            self.statusBar().showMessage("Serveur non connecté - affichage non actualisé")

    def trigger_emergency(self, road):
        if self.connected:
            self.control_panel.add_event("Demande d'urgence : " + road)
            self.command_requested.emit("trigger_emergency", {"road": road})

    def clear_emergency(self):
        if self.connected:
            self.control_panel.add_event("Demande de fin d'urgence")
            self.command_requested.emit("clear_emergency", {})

    def set_rush_hour(self, actif):
        if self.connected:
            self.control_panel.add_event("Demande d'heure de pointe : " + ("activer" if actif else "désactiver"))
            self.command_requested.emit("set_rush_hour", {"value": actif})

    def set_strategy(self, strategie):
        if self.connected:
            self.control_panel.add_event("Demande de stratégie : " + strategie)
            self.command_requested.emit("set_strategy", {"value": strategie})

    def closeEvent(self, event):
        self.carrefour_widget.repaint_timer.stop()
        super().closeEvent(event)
