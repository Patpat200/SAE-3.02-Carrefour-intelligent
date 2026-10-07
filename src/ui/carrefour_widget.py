from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt
from .vehicle_widget import couleur_vehicule


class CarrefourWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {
            "feux": [],
            "vehicules": [],
            "densite": {},
        }
        self.setMinimumSize(400, 400)

    def set_state(self, state):
        if not state:
            return
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        self.largeur = self.width()
        self.hauteur = self.height()
        self.centre_x = self.largeur // 2
        self.centre_y = self.hauteur // 2

        painter.fillRect(self.rect(), QColor("#d8d2c4"))
        self.dessiner_routes(painter)
        self.dessiner_marquage(painter)
        self.dessiner_vehicules(painter)
        self.dessiner_feux(painter)
        self.dessiner_panneaux(painter)

    def dessiner_routes(self, painter):
        cx = self.centre_x
        cy = self.centre_y

        painter.setBrush(QBrush(QColor("#bfbfbf")))
        painter.drawRect(cx - 62, 0, 124, self.hauteur)
        painter.drawRect(0, cy - 62, self.largeur, 124)

        painter.setBrush(QBrush(QColor("#6f7377")))
        painter.drawRect(cx - 50, 0, 100, self.hauteur)
        painter.drawRect(0, cy - 50, self.largeur, 100)

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

        for feu in self.state.get("feux", []):
            pos_x, pos_y = positions_feux[feu["nom"]]
            couleur = couleurs.get(feu["etat"], QColor("black"))

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
        for vehicle in self.state.get("vehicules", []):
            longueur = vehicle["longueur"]
            x, y, angle = self.position_voiture(
                vehicle["voie"], vehicle["position"], longueur
            )
            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            painter.setBrush(QBrush(couleur_vehicule(vehicle)))
            painter.drawRoundedRect(-10, -longueur // 2, 20, longueur, 4, 4)
            painter.setBrush(QBrush(QColor("#9fd3ff")))
            painter.drawRect(-7, -longueur // 2 + 6, 14, 5)
            painter.restore()

    def dessiner_panneaux(self, painter):
        painter.setPen(QColor("#333333"))
        painter.drawText(8, self.centre_y + 90, "Route de Neuf-Brisach (D 418)")
        painter.save()
        painter.translate(self.centre_x + 90, self.centre_y - 90)
        painter.rotate(-90)
        painter.drawText(0, 0, "Avenue d'Alsace (D 201)")
        painter.restore()
