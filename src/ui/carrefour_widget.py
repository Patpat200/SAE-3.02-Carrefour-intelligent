from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt

class CarrefourWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.state = {
            "feux": [],
        }
        self.setMinimumSize(400, 400)

    def set_state(self, state):
        if not state:
            return
        self.state = state
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor("lightgreen"))

        largeur = self.width()
        hauteur = self.height()
        centre_x = largeur // 2
        centre_y = hauteur // 2
        taille_route = 100

        painter.setBrush(QBrush(QColor("gray")))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRect(centre_x - taille_route // 2, 0, taille_route, hauteur)
        painter.drawRect(0, centre_y - taille_route // 2, largeur, taille_route)

        decalage_feu = 58
        decalage_voie = 25

        positions_feux = {
            "Nord": (centre_x - decalage_voie, centre_y - decalage_feu),
            "Sud": (centre_x + decalage_voie, centre_y + decalage_feu),
            "Ouest": (centre_x - decalage_feu, centre_y + decalage_voie),
            "Est": (centre_x + decalage_feu, centre_y - decalage_voie),
        }

        couleurs = {
            "VERT": QColor("green"),
            "ORANGE": QColor("orange"),
            "ROUGE": QColor("red"),
            "PRIORITAIRE": QColor("blue")
        }

        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(centre_x - 50, centre_y - 70, 50, 3)
        painter.drawRect(centre_x, centre_y + 67, 50, 3)
        painter.drawRect(centre_x - 70, centre_y, 3, 50)
        painter.drawRect(centre_x + 67, centre_y - 50, 3, 50)

        for feu in self.state.get("feux", []):
            pos_x, pos_y = positions_feux[feu["nom"]]
            couleur = couleurs.get(feu["etat"], QColor("black"))

            painter.setBrush(QBrush(QColor("black")))
            painter.drawEllipse(pos_x - 9, pos_y - 9, 18, 18)
            painter.setBrush(QBrush(couleur))
            painter.drawEllipse(pos_x - 6, pos_y - 6, 12, 12)
