from PyQt6.QtWidgets import QGroupBox, QLabel, QPushButton, QVBoxLayout


class ControlPanel(QGroupBox):
    def __init__(self):
        super().__init__("Panneau de contrôle")

        self.status_label = QLabel("Connexion: en attente...")
        self.density_label = QLabel("Trafic: en attente...")
        self.emergency_label = QLabel("Aucune urgence")

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.density_label)
        layout.addWidget(self.emergency_label)

        bouton_nord = QPushButton("Urgence Nord")
        bouton_nord.setEnabled(False)
        layout.addWidget(bouton_nord)

        bouton_sud = QPushButton("Urgence Sud")
        bouton_sud.setEnabled(False)
        layout.addWidget(bouton_sud)

        bouton_est = QPushButton("Urgence Est")
        bouton_est.setEnabled(False)
        layout.addWidget(bouton_est)

        bouton_ouest = QPushButton("Urgence Ouest")
        bouton_ouest.setEnabled(False)
        layout.addWidget(bouton_ouest)

        clear_button = QPushButton("Fin urgence")
        clear_button.setEnabled(False)
        layout.addWidget(clear_button)

        layout.addStretch()
        self.setLayout(layout)
