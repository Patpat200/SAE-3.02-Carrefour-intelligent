import time

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QTimer
from .vehicle_widget import couleur_vehicule

NOM_VILLE = "Colmar"
RUE_NORD_SUD = "Avenue d'Alsace (D 201)"
RUE_EST_OUEST = "Route de Neuf-Brisach (D 418)"
DIRECTION_SUD = "Mulhouse"
DIRECTION_EST = "Neuf-Brisach - Freiburg"
DIRECTION_OUEST = "Centre ville"


class CarrefourWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.state = {
            "feux": [],
            "vehicules": [],
            "densite": {},
        }
        self.setMinimumSize(500, 500)
        self.decor_visible = True
        self.data_message = "En attente du serveur"
        self.data_stale = True
        self.selected_vehicle_id = ""

        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(150)

    def set_state(self, state):
        if not state:
            return
        self.state = state
        self.update()

    def set_decor_visible(self, visible):
        self.decor_visible = visible
        self.update()

    def set_selected_vehicle(self, identifier):
        self.selected_vehicle_id = identifier
        self.update()

    def set_data_message(self, message, stale):
        if (message, stale) != (self.data_message, self.data_stale):
            self.data_message = message
            self.data_stale = stale
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.fillRect(self.rect(), QColor("#d8d2c4"))
        taille = min(self.width(), self.height())
        painter.translate((self.width() - taille) / 2, (self.height() - taille) / 2)
        painter.scale(taille / 700, taille / 700)
        self.largeur = 700
        self.hauteur = 700
        self.centre_x = self.largeur // 2
        self.centre_y = self.hauteur // 2

        if self.decor_visible:
            self.dessiner_decor(painter)
        self.dessiner_routes(painter)
        self.dessiner_marquage(painter)
        self.dessiner_vehicules(painter)
        self.dessiner_feux(painter)
        self.dessiner_panneaux(painter)
        painter.setFont(QFont("Arial", 9))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#855800" if self.data_stale else "#1e663a"))
        largeur = painter.fontMetrics().horizontalAdvance(self.data_message) + 16
        painter.drawRoundedRect(8, 670, largeur, 23, 3, 3)
        painter.setPen(QColor("white"))
        painter.drawText(16, 686, self.data_message)

    def dessiner_decor(self, painter):
        cx = self.centre_x
        cy = self.centre_y

        painter.fillRect(0, 0, self.largeur, self.hauteur, QColor("#d8d2c4"))

        self.dessiner_batiment(painter, cx - 190, cy - 170, 100, 60, "#b5654a")
        self.dessiner_batiment(painter, cx - 300, cy - 150, 80, 70, "#8c8c8c")
        self.dessiner_batiment(painter, cx + 90, cy - 190, 70, 100, "#c27c4e")
        self.dessiner_batiment(painter, cx + 190, cy - 150, 110, 60, "#9a9a9a")
        self.dessiner_batiment(painter, cx + 90, cy + 100, 130, 70, "#a8553c")
        self.dessiner_batiment(painter, cx + 250, cy + 110, 60, 90, "#8c8c8c")

        painter.setBrush(QBrush(QColor("#9ccc7a")))
        painter.drawRect(cx - 320, cy + 80, 240, self.hauteur)
        for i in range(4):
            for j in range(3):
                self.dessiner_arbre(painter, cx - 290 + i * 55, cy + 115 + j * 60)

    def dessiner_batiment(self, painter, x, y, w, h, couleur):
        painter.setBrush(QBrush(QColor("#a09a8c")))
        painter.drawRect(x + 4, y + 4, w, h)
        painter.setBrush(QBrush(QColor(couleur)))
        painter.drawRect(x, y, w, h)
        painter.setPen(QPen(QColor(0, 0, 0, 60), 2))
        if w > h:
            painter.drawLine(x + 6, y + h // 2, x + w - 6, y + h // 2)
        else:
            painter.drawLine(x + w // 2, y + 6, x + w // 2, y + h - 6)
        painter.setPen(Qt.PenStyle.NoPen)

    def dessiner_arbre(self, painter, x, y):
        painter.setBrush(QBrush(QColor("#4f8a3c")))
        painter.drawEllipse(x - 9, y - 9, 18, 18)
        painter.setBrush(QBrush(QColor("#3b6e2c")))
        painter.drawEllipse(x - 4, y - 5, 8, 8)

    def dessiner_routes(self, painter):
        cx = self.centre_x
        cy = self.centre_y

        painter.setBrush(QBrush(QColor("#bfbfbf")))
        painter.drawRect(cx - 62, 0, 124, self.hauteur)
        painter.drawRect(0, cy - 62, self.largeur, 124)

        painter.setBrush(QBrush(QColor("#6f7377")))
        painter.drawRect(cx - 50, 0, 100, self.hauteur)
        painter.drawRect(0, cy - 50, self.largeur, 100)

        painter.setBrush(QBrush(QColor("#7f9a84")))
        painter.drawRect(cx - 50, 0, 9, cy - 72)
        painter.drawRect(cx + 41, 0, 9, cy - 72)
        painter.drawRect(cx - 50, cy + 72, 9, self.hauteur)
        painter.drawRect(cx + 41, cy + 72, 9, self.hauteur)

        painter.setBrush(QBrush(QColor("#8fbf6e")))
        painter.drawRect(cx - 4, 0, 8, cy - 80)
        painter.drawRect(cx - 4, cy + 80, 8, self.hauteur)
        y = cy - 110
        while y > 0:
            self.dessiner_arbre(painter, cx, y)
            y = y - 50
        y = cy + 110
        while y < self.hauteur:
            self.dessiner_arbre(painter, cx, y)
            y = y + 50

    def dessiner_marquage(self, painter):
        cx = self.centre_x
        cy = self.centre_y
        painter.setBrush(QBrush(QColor("white")))

        x = cx - 90
        while x > 0:
            painter.drawRect(x - 14, cy - 1, 14, 2)
            x = x - 28
        x = cx + 90
        while x < self.largeur:
            painter.drawRect(x, cy - 1, 14, 2)
            x = x + 28

        for i in range(8):
            decalage = -46 + i * 12
            painter.drawRect(cx + decalage, cy - 65, 7, 13)
            painter.drawRect(cx + decalage, cy + 52, 7, 13)
            painter.drawRect(cx - 65, cy + decalage, 13, 7)
            painter.drawRect(cx + 52, cy + decalage, 13, 7)

        painter.drawRect(cx - 50, cy - 70, 50, 3)
        painter.drawRect(cx, cy + 67, 50, 3)
        painter.drawRect(cx - 70, cy, 3, 50)
        painter.drawRect(cx + 67, cy - 50, 3, 50)

    def dessiner_feux(self, painter):
        cx = self.centre_x
        cy = self.centre_y

        positions_feux = {
            "Nord": (cx - 58, cy - 76),
            "Sud": (cx + 58, cy + 76),
            "Ouest": (cx - 76, cy + 58),
            "Est": (cx + 76, cy - 58),
        }

        couleurs = {
            "VERT": QColor("#27c93f"),
            "ORANGE": QColor("orange"),
            "ROUGE": QColor("red"),
            "PRIORITAIRE": QColor("#2f6bff"),
        }

        etats = {feu["nom"]: feu["etat"] for feu in self.state.get("feux", [])}
        for nom in positions_feux:
            feu = {"nom": nom, "etat": etats.get(nom, "INCONNU")}
            pos_x, pos_y = positions_feux[feu["nom"]]
            couleur = couleurs.get(feu["etat"], QColor("#777777"))

            painter.setBrush(QBrush(QColor("#1e1e1e")))
            painter.drawRoundedRect(pos_x - 9, pos_y - 9, 18, 18, 4, 4)
            painter.setBrush(QBrush(couleur))
            painter.drawEllipse(pos_x - 6, pos_y - 6, 12, 12)

    def position_voiture(self, voie, position, longueur, decalage=0):
        milieu = position - longueur / 2
        cote = 25 + decalage
        if voie == "Nord":
            return [self.centre_x - cote, self.centre_y + milieu, 180]
        if voie == "Sud":
            return [self.centre_x + cote, self.centre_y - milieu, 0]
        if voie == "Ouest":
            return [self.centre_x + milieu, self.centre_y + cote, 90]
        return [self.centre_x - milieu, self.centre_y - cote, 270]

    def dessiner_vehicules(self, painter):
        clignote = int(time.monotonic() * 3) % 2 == 0

        for index, vehicle in enumerate(self.state.get("vehicules", [])):
            longueur = vehicle["longueur"]
            place = self.position_voiture(
                vehicle["voie"], vehicle["position"], longueur, vehicle.get("decalage", 0)
            )
            x = place[0]
            y = place[1]
            angle = place[2] + 9 * vehicle.get("braquage", 0)

            reste = vehicle.get("virage", 0)
            if reste > 0:
                ancienne = self.position_voiture(
                    vehicle["ancienne_voie"], vehicle["ancienne_position"], longueur
                )
                ecart = angle - ancienne[2]
                if ecart > 180:
                    ecart -= 360
                if ecart < -180:
                    ecart += 360
                x = x + (ancienne[0] - x) * reste
                y = y + (ancienne[1] - y) * reste
                angle = angle - ecart * reste

            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            painter.setBrush(QBrush(couleur_vehicule(vehicle)))

            if vehicle.get("urgence"):
                self.dessiner_urgence(painter, longueur)
            else:
                painter.drawRoundedRect(-10, -longueur // 2, 20, longueur, 4, 4)
                painter.setBrush(QBrush(QColor("#9fd3ff")))
                painter.drawRect(-7, -longueur // 2 + 6, 14, 5)

                painter.setBrush(QBrush(QColor("orange")))
                if clignote and vehicle.get("direction") == "gauche":
                    painter.drawRect(-10, -longueur // 2, 5, 4)
                if clignote and vehicle.get("direction") == "droite":
                    painter.drawRect(5, -longueur // 2, 5, 4)

            identifier = str(vehicle.get("id", "vehicule-" + str(index)))
            if identifier == self.selected_vehicle_id:
                painter.setPen(QPen(QColor("magenta"), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(-13, -longueur // 2 - 3, 26, longueur + 6, 4, 4)
            painter.restore()

    def dessiner_urgence(self, painter, longueur):
        painter.setPen(QPen(QColor("yellow"), 2))
        painter.drawRect(-10, -longueur // 2, 20, longueur)
        painter.setPen(Qt.PenStyle.NoPen)

        if int(time.monotonic() * 6) % 2 == 0:
            couleur_1 = QColor("blue")
            couleur_2 = QColor("white")
        else:
            couleur_1 = QColor("white")
            couleur_2 = QColor("blue")

        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(-9, -4, 18, 8)
        painter.setBrush(QBrush(couleur_1))
        painter.drawRect(-8, -3, 6, 6)
        painter.setBrush(QBrush(couleur_2))
        painter.drawRect(2, -3, 6, 6)

    def dessiner_panneau(self, painter, x, y, texte):
        largeur_texte = painter.fontMetrics().horizontalAdvance(texte)
        painter.setPen(QPen(QColor("#1e1e1e"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(x, y, largeur_texte + 12, 18, 3, 3)
        painter.drawText(x + 6, y + 13, texte)
        painter.setPen(Qt.PenStyle.NoPen)

    def dessiner_panneaux(self, painter):
        cx = self.centre_x
        cy = self.centre_y
        painter.setFont(QFont("Arial", 8))

        self.dessiner_panneau(painter, cx + 70, self.hauteur - 26, "↓ " + DIRECTION_SUD)
        largeur_texte = painter.fontMetrics().horizontalAdvance(DIRECTION_EST + " →")
        self.dessiner_panneau(
            painter, self.largeur - largeur_texte - 20, cy + 68, DIRECTION_EST + " →"
        )
        self.dessiner_panneau(painter, 8, cy - 86, "← " + DIRECTION_OUEST)

        painter.setPen(QColor("#333333"))
        painter.drawText(8, cy + 76, RUE_EST_OUEST)
        painter.save()
        painter.translate(cx + 74, cy - 92)
        painter.rotate(-90)
        painter.drawText(0, 0, RUE_NORD_SUD)
        painter.restore()

        police = QFont("Arial", 9)
        police.setBold(True)
        painter.setFont(police)
        titre = NOM_VILLE + " - Avenue d'Alsace / Route de Neuf-Brisach"
        largeur_texte = painter.fontMetrics().horizontalAdvance(titre)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 215)))
        painter.drawRect(0, 0, largeur_texte + 16, 24)
        painter.setPen(QColor("#333333"))
        painter.drawText(8, 16, titre)
        painter.setPen(Qt.PenStyle.NoPen)
