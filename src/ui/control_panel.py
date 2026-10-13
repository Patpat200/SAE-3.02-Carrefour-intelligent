from PyQt6.QtWidgets import QGroupBox, QLabel, QPushButton, QVBoxLayout


class ControlPanel(QGroupBox):
    def __init__(
        self,
        on_trigger_emergency,
        on_clear_emergency,
        on_set_rush_hour,
        on_set_strategy,
    ):
        super().__init__("Panneau de contrôle")
        self.on_trigger_emergency = on_trigger_emergency
        self.on_set_rush_hour = on_set_rush_hour
        self.on_set_strategy = on_set_strategy
        self.heure_de_pointe = False
        self.strategie = "fixe"

        self.status_label = QLabel("Connexion: en attente...")
        self.density_label = QLabel("Trafic: en attente...")
        self.help_label = QLabel("Urgence: rouge, bande blanche, gyrophare bleu")
        self.emergency_label = QLabel("Urgence : en attente...")
        self.trafic_label = QLabel("Trafic : en attente...")
        self.setMinimumWidth(240)
        self.status_label.setWordWrap(True)
        self.density_label.setWordWrap(True)
        self.emergency_label.setWordWrap(True)
        self.help_label.setWordWrap(True)
        self.trafic_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.density_label)
        layout.addWidget(self.help_label)
        layout.addWidget(self.emergency_label)

        bouton_nord = QPushButton("Urgence Nord")
        bouton_nord.clicked.connect(self.urgence_nord)
        layout.addWidget(bouton_nord)

        bouton_sud = QPushButton("Urgence Sud")
        bouton_sud.clicked.connect(self.urgence_sud)
        layout.addWidget(bouton_sud)

        bouton_est = QPushButton("Urgence Est")
        bouton_est.clicked.connect(self.urgence_est)
        layout.addWidget(bouton_est)

        bouton_ouest = QPushButton("Urgence Ouest")
        bouton_ouest.clicked.connect(self.urgence_ouest)
        layout.addWidget(bouton_ouest)

        clear_button = QPushButton("Fin urgence")
        clear_button.clicked.connect(on_clear_emergency)
        layout.addWidget(clear_button)

        layout.addWidget(self.trafic_label)
        self.bouton_pointe = QPushButton("Activer l'heure de pointe")
        self.bouton_pointe.clicked.connect(self.changer_heure_de_pointe)
        layout.addWidget(self.bouton_pointe)

        self.bouton_strategie = QPushButton("Feux : fixes")
        self.bouton_strategie.clicked.connect(self.changer_strategie)
        layout.addWidget(self.bouton_strategie)

        layout.addStretch()
        self.setLayout(layout)

    def urgence_nord(self):
        self.on_trigger_emergency("Nord")

    def urgence_sud(self):
        self.on_trigger_emergency("Sud")

    def urgence_est(self):
        self.on_trigger_emergency("Est")

    def urgence_ouest(self):
        self.on_trigger_emergency("Ouest")

    def changer_heure_de_pointe(self):
        self.on_set_rush_hour(not self.heure_de_pointe)

    def changer_strategie(self):
        if self.strategie == "fixe":
            self.on_set_strategy("adaptatif")
        else:
            self.on_set_strategy("fixe")

    def set_trafic(self, trafic):
        self.heure_de_pointe = trafic.get("heure_de_pointe", False)
        if self.heure_de_pointe:
            texte = "Heure simulée : " + trafic.get("heure", "")
            texte = texte + "\nTrafic x" + str(trafic.get("niveau", 1))
            self.trafic_label.setText(texte)
            self.bouton_pointe.setText("Désactiver l'heure de pointe")
        else:
            self.trafic_label.setText("Trafic normal (constant)")
            self.bouton_pointe.setText("Activer l'heure de pointe")

    def set_strategie(self, strategie):
        self.strategie = strategie
        if strategie == "adaptatif":
            self.bouton_strategie.setText("Feux : adaptatifs")
        else:
            self.bouton_strategie.setText("Feux : fixes")

    def set_status(self, connected, error_message=""):
        for bouton in self.findChildren(QPushButton):
            bouton.setEnabled(connected)
        if connected:
            self.status_label.setText("Connexion: connectée")
            self.status_label.setStyleSheet("color: green;")
            return

        if error_message:
            self.status_label.setText("Connexion: " + error_message)
        else:
            self.status_label.setText("Connexion: déconnectée")
        self.status_label.setStyleSheet("color: red;")

    def set_density(self, density):
        if not density:
            self.density_label.setText("Trafic: en attente...")
            return
        text = "Véhicules :"
        for voie in density:
            text = text + " " + voie[0] + " " + str(density[voie])
        self.density_label.setText(text)

    def set_emergency(self, road):
        if road:
            self.emergency_label.setText("URGENCE ACTIVE: " + road)
            self.emergency_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.emergency_label.setText("Aucune urgence")
            self.emergency_label.setStyleSheet("")
