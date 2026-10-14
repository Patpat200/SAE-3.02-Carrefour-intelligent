from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt

# Largeur d'un vehicule (meme valeur que Vehicule.LARGEUR cote serveur).
# On la redefinit ici : le client ne doit pas importer le code du serveur.
LARGEUR_VEHICULE = 20


class CarrefourWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.state = {
            "feux": [],
            "vehicules": [],
        }
        self.setMinimumSize(400, 400)

    def set_state(self, state):
        if not state:
            return
        self.state = state
        self.update()

    def rectangle_vehicule(self, voie, position, longueur):
        """Rectangle (x, y, largeur, hauteur) du vehicule, relatif au centre du carrefour."""
        avant = position
        arriere = position - longueur
        if voie == "Nord":
            return (-35, arriere, LARGEUR_VEHICULE, longueur)
        if voie == "Sud":
            return (15, -avant, LARGEUR_VEHICULE, longueur)
        if voie == "Ouest":
            return (arriere, 15, longueur, LARGEUR_VEHICULE)
        return (-avant, -35, longueur, LARGEUR_VEHICULE)

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

        # --- Vehicules (envoyes par le serveur) ---
        for vehicule in self.state.get("vehicules", []):
            x, y, w, h = self.rectangle_vehicule(
                vehicule["voie"], vehicule["position"], vehicule["longueur"]
            )
            couleur = QColor(vehicule.get("couleur", "black"))
            if not couleur.isValid():
                couleur = QColor("black")

            painter.setBrush(QBrush(couleur))
            if vehicule.get("urgence"):
                painter.setPen(QPen(QColor("blue"), 3))
            else:
                painter.setPen(QPen(QColor("black"), 1))
            painter.drawRect(int(centre_x + x), int(centre_y + y), int(w), int(h))

        painter.setPen(Qt.PenStyle.NoPen)

        for feu in self.state.get("feux", []):
            pos_x, pos_y = positions_feux[feu["nom"]]
            couleur = couleurs.get(feu["etat"], QColor("black"))

            painter.setBrush(QBrush(QColor("black")))
            painter.drawEllipse(pos_x - 9, pos_y - 9, 18, 18)
            painter.setBrush(QBrush(couleur))
            painter.drawEllipse(pos_x - 6, pos_y - 6, 12, 12)