from datetime import datetime
from PyQt6.QtCore import Qt

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFormLayout, QGridLayout, QGroupBox, QHeaderView,
    QLabel, QListWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)


class ControlPanel(QGroupBox):
    def __init__(self, on_trigger_emergency, on_clear_emergency,
                 on_set_rush_hour, on_set_strategy):
        super().__init__("Panneau de contrôle")
        self.on_trigger_emergency = on_trigger_emergency
        self.on_set_rush_hour = on_set_rush_hour
        self.on_set_strategy = on_set_strategy
        self.heure_de_pointe = False
        self.strategie = None
        self.connected = False
        self.trafic_available = False
        self.command_buttons = []
        self.setMinimumWidth(290)

        self.status_label = QLabel("Connexion : en attente...")
        self.status_label.setWordWrap(True)
        self.last_update_label = QLabel("Aucune donnée reçue")
        self.last_update_label.setWordWrap(True)
        self.data_status_label = QLabel("En attente des données du serveur")
        self.data_status_label.setWordWrap(True)
        self.tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.last_update_label)
        layout.addWidget(self.data_status_label)
        layout.addWidget(self.tabs)

        suivi = QWidget()
        suivi_layout = QVBoxLayout(suivi)
        self.table_voies = QTableWidget(4, 3)
        self.table_voies.setHorizontalHeaderLabels(["Voie", "Voitures", "Feu"])
        self.table_voies.verticalHeader().hide()
        self.table_voies.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_voies.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_voies.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table_voies.setFixedHeight(155)
        for ligne, voie in enumerate(["Nord", "Sud", "Est", "Ouest"]):
            self.table_voies.setItem(ligne, 0, QTableWidgetItem(voie))
            self.table_voies.setItem(ligne, 1, QTableWidgetItem("—"))
            self.table_voies.setItem(ligne, 2, QTableWidgetItem("—"))
        suivi_layout.addWidget(QLabel("État des quatre voies"))
        suivi_layout.addWidget(self.table_voies)
        self.emergency_label = QLabel("Urgence : en attente...")
        self.trafic_label = QLabel("Trafic : en attente...")
        self.strategie_label = QLabel("Stratégie : en attente...")
        for label in [self.emergency_label, self.trafic_label, self.strategie_label]:
            label.setWordWrap(True)
            suivi_layout.addWidget(label)
        legende = QLabel("Feu bleu : passage prioritaire\nVéhicule rouge : véhicule d'urgence")
        legende.setWordWrap(True)
        suivi_layout.addWidget(legende)
        self.decor_checkbox = QCheckBox("Afficher les bâtiments et le parc")
        self.decor_checkbox.setChecked(True)
        suivi_layout.addWidget(self.decor_checkbox)
        self.capture_button = QPushButton("Enregistrer une capture du carrefour")
        suivi_layout.addWidget(self.capture_button)
        suivi_layout.addStretch()
        self.tabs.addTab(suivi, "Suivi")

        commandes = QWidget()
        commandes_layout = QVBoxLayout(commandes)
        commandes_layout.addWidget(QLabel("Demander un passage prioritaire"))
        grille = QGridLayout()
        for numero, voie in enumerate(["Nord", "Sud", "Est", "Ouest"]):
            bouton = QPushButton("Urgence " + voie)
            bouton.clicked.connect(lambda checked=False, road=voie: self.on_trigger_emergency(road))
            grille.addWidget(bouton, numero // 2, numero % 2)
            self.command_buttons.append(bouton)
        commandes_layout.addLayout(grille)
        bouton_fin = QPushButton("Fin urgence")
        bouton_fin.clicked.connect(on_clear_emergency)
        commandes_layout.addWidget(bouton_fin)
        self.command_buttons.append(bouton_fin)
        commandes_layout.addWidget(QLabel("Réglages du trafic"))
        self.bouton_pointe = QPushButton("Activer l'heure de pointe")
        self.bouton_pointe.clicked.connect(self.changer_heure_de_pointe)
        self.bouton_strategie = QPushButton("Feux : en attente...")
        self.bouton_strategie.clicked.connect(self.changer_strategie)
        for bouton in [self.bouton_pointe, self.bouton_strategie]:
            commandes_layout.addWidget(bouton)
            self.command_buttons.append(bouton)
        aide = QLabel("Les demandes seront transmises au serveur. L'affichage attend ses nouvelles données.")
        aide.setWordWrap(True)
        commandes_layout.addWidget(aide)
        self.command_status_label = QLabel("Aucune demande en attente")
        self.command_status_label.setWordWrap(True)
        self.command_status_label.setTextFormat(Qt.TextFormat.PlainText)
        commandes_layout.addWidget(self.command_status_label)
        commandes_layout.addStretch()
        self.tabs.addTab(commandes, "Commandes")

        historique = QWidget()
        historique_layout = QVBoxLayout(historique)
        self.history_list = QListWidget()
        historique_layout.addWidget(self.history_list)
        self.export_history_button = QPushButton("Exporter l'historique en texte")
        historique_layout.addWidget(self.export_history_button)
        self.clear_history_button = QPushButton("Effacer l'historique")
        self.clear_history_button.clicked.connect(self.history_list.clear)
        historique_layout.addWidget(self.clear_history_button)
        self.tabs.addTab(historique, "Historique")

        connexion = QWidget()
        connexion_layout = QVBoxLayout(connexion)
        formulaire = QFormLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Exemple : 192.168.1.20")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        formulaire.addRow("Adresse du serveur", self.host_input)
        formulaire.addRow("Port TCP", self.port_input)
        connexion_layout.addLayout(formulaire)
        self.connect_button = QPushButton("Se connecter / Réessayer")
        self.disconnect_button = QPushButton("Se déconnecter")
        connexion_layout.addWidget(self.connect_button)
        connexion_layout.addWidget(self.disconnect_button)
        aide_connexion = QLabel("Utiliser l'adresse IP du PC qui lance le serveur. Les paramètres sont mémorisés à la connexion. Une connexion perdue est retentée automatiquement, sauf après une déconnexion volontaire.")
        aide_connexion.setWordWrap(True)
        connexion_layout.addWidget(aide_connexion)
        connexion_layout.addStretch()
        self.tabs.addTab(connexion, "Connexion")

    def set_data_age(self, age, connected):
        if age is None:
            texte = "En attente des données du serveur"
            couleur = "#855800"
        elif not connected:
            texte = "Affichage non actualisé : serveur déconnecté"
            couleur = "#b92020"
        elif age >= 3:
            texte = "Aucune nouvelle donnée depuis " + str(int(age)) + " s"
            couleur = "#855800"
        else:
            texte = "Données actualisées"
            couleur = "#167d27"
        self.data_status_label.setText(texte)
        self.data_status_label.setStyleSheet("color: " + couleur + ";")
        return texte

    def add_event(self, texte):
        heure = datetime.now().strftime("%H:%M:%S")
        self.history_list.addItem(heure + " - " + texte)
        if self.history_list.count() > 100:
            self.history_list.takeItem(0)
        self.history_list.scrollToBottom()

    def changer_heure_de_pointe(self):
        self.on_set_rush_hour(not self.heure_de_pointe)

    def changer_strategie(self):
        if self.strategie == "fixe":
            self.on_set_strategy("adaptatif")
        else:
            self.on_set_strategy("fixe")

    def set_trafic(self, trafic):
        self.trafic_available = bool(trafic)
        self.bouton_pointe.setEnabled(self.connected and self.trafic_available)
        self.heure_de_pointe = trafic.get("heure_de_pointe", False)
        if not trafic:
            self.trafic_label.setText("Trafic : en attente...")
        elif self.heure_de_pointe:
            self.trafic_label.setText("Heure simulée : " + trafic.get("heure", "") +
                                      "\nTrafic x" + str(trafic.get("niveau", 1)))
        else:
            self.trafic_label.setText("Trafic normal (constant)")
        if self.heure_de_pointe:
            self.bouton_pointe.setText("Désactiver l'heure de pointe")
        else:
            self.bouton_pointe.setText("Activer l'heure de pointe")

    def set_strategie(self, strategie):
        self.strategie = strategie
        self.bouton_strategie.setEnabled(self.connected and strategie in ["fixe", "adaptatif"])
        if strategie is None:
            self.bouton_strategie.setText("Feux : en attente...")
            self.strategie_label.setText("Stratégie : en attente...")
        elif strategie == "adaptatif":
            self.bouton_strategie.setText("Feux : adaptatifs")
            self.strategie_label.setText("Stratégie : feux adaptatifs")
        else:
            self.bouton_strategie.setText("Feux : fixes")
            self.strategie_label.setText("Stratégie : feux fixes")

    def set_status(self, connected, error_message=""):
        self.connected = connected
        for bouton in self.command_buttons:
            bouton.setEnabled(connected)
        self.bouton_pointe.setEnabled(connected and self.trafic_available)
        self.bouton_strategie.setEnabled(connected and self.strategie in ["fixe", "adaptatif"])
        if connected:
            self.status_label.setText("Connexion : connectée")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("Connexion : " + (error_message or "déconnectée"))
            self.status_label.setStyleSheet("color: red;")

    def set_density(self, density):
        for ligne, voie in enumerate(["Nord", "Sud", "Est", "Ouest"]):
            self.table_voies.item(ligne, 1).setText(str(density.get(voie, "—")))

    def set_feux(self, feux):
        etats = {feu["nom"]: feu["etat"] for feu in feux}
        couleurs = {"VERT": "#167d27", "ORANGE": "#995c00",
                    "ROUGE": "#b92020", "PRIORITAIRE": "#245acc"}
        for ligne, voie in enumerate(["Nord", "Sud", "Est", "Ouest"]):
            etat = etats.get(voie, "—")
            cellule = self.table_voies.item(ligne, 2)
            cellule.setText(etat.lower())
            cellule.setForeground(QColor(couleurs.get(etat, "#555555")))
            cellule.setToolTip(voie + " : " + etat.lower())

    def set_emergency(self, road):
        if road:
            self.emergency_label.setText("URGENCE ACTIVE : " + road)
            self.emergency_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.emergency_label.setText("Aucune urgence")
            self.emergency_label.setStyleSheet("")
