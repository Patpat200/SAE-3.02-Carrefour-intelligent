from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QLabel, QPushButton, QVBoxLayout


class ControlPanel(QGroupBox):
    """Panneau de controle : affiche l'etat et emet des signaux quand on clique."""

    emergency_requested = pyqtSignal(str)   # nom de la voie (ex: "Nord")
    clear_requested = pyqtSignal()

    VOIES = ["Nord", "Sud", "Est", "Ouest"]

    def __init__(self):
        super().__init__("Panneau de contrôle")

        self.status_label = QLabel("Connexion: en attente...")
        self.density_label = QLabel("Trafic: en attente...")
        self.emergency_label = QLabel("Aucune urgence")

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.density_label)
        layout.addWidget(self.emergency_label)

        # Un bouton par voie, desactive tant qu'on n'est pas connecte au serveur
        self.urgence_buttons = {}
        for voie in self.VOIES:
            bouton = QPushButton("Urgence " + voie)
            bouton.setEnabled(False)
            bouton.clicked.connect(
                lambda checked=False, v=voie: self.emergency_requested.emit(v)
            )
            layout.addWidget(bouton)
            self.urgence_buttons[voie] = bouton

        self.clear_button = QPushButton("Fin urgence")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        layout.addWidget(self.clear_button)

        layout.addStretch()
        self.setLayout(layout)

    def set_connected(self, connected, error=""):
        """Met a jour le texte de connexion et active/desactive les boutons."""
        if connected:
            self.status_label.setText("Connexion: connecté")
        elif error:
            self.status_label.setText("Connexion: " + error)
        else:
            self.status_label.setText("Connexion: en attente...")

        for bouton in self.urgence_buttons.values():
            bouton.setEnabled(connected)
        self.clear_button.setEnabled(connected)

    def set_emergency(self, voie):
        """voie = nom de la voie en urgence, ou None s'il n'y en a pas."""
        if voie:
            self.emergency_label.setText("Urgence: " + voie)
        else:
            self.emergency_label.setText("Aucune urgence")

    def set_traffic(self, text):
        self.density_label.setText(text)