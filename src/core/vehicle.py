import random


class Vehicule:

    LONGUEUR = 30
    LARGEUR = 20
    DEPART = -180
    FIN = 300
    LIGNE_ARRET = -70
    BORD_CARREFOUR = 50
    ECART_MIN = 10
    POINT_DROITE = -25
    POINT_GAUCHE = 25

    COULEURS = ["blue", "white", "yellow", "purple", "black", "darkgreen"]
    DIRECTIONS = ["tout_droit", "tout_droit", "gauche", "droite"]

    # la voie qu'on rejoint quand on tourne
    VOIE_A_DROITE = {"Nord": "Est", "Sud": "Ouest", "Ouest": "Nord", "Est": "Sud"}
    VOIE_A_GAUCHE = {"Nord": "Ouest", "Sud": "Est", "Ouest": "Sud", "Est": "Nord"}
    VOIE_EN_FACE = {"Nord": "Sud", "Sud": "Nord", "Ouest": "Est", "Est": "Ouest"}

    def __init__(self, voie, urgence=False):
        self.voie = voie
        self.origine = voie
        self.urgence = urgence
        self.position = self.DEPART
        self.arrete = False
        self.identifiant = "voiture-" + str(id(self))

        if urgence:
            self.vitesse = random.randint(4, 6)
            self.couleur = "red"
            self.direction = "tout_droit"
            self.identifiant = "urgence-" + str(id(self))
        else:
            self.vitesse = random.randint(2, 4)
            self.couleur = random.choice(self.COULEURS)
            self.direction = random.choice(self.DIRECTIONS)

    def avancer(self, feu, devant=None):
        nouvelle_pos = self.position + self.vitesse

        if feu.etat == "ROUGE" or feu.etat == "ORANGE":
            if self.position <= self.LIGNE_ARRET:
                nouvelle_pos = min(nouvelle_pos, self.LIGNE_ARRET)

        if devant is not None:
            limite = devant.position - self.LONGUEUR - self.ECART_MIN
            nouvelle_pos = min(nouvelle_pos, limite)

        if self.direction == "droite":
            nouvelle_pos = min(nouvelle_pos, self.POINT_DROITE)
        if self.direction == "gauche":
            nouvelle_pos = min(nouvelle_pos, self.POINT_GAUCHE)

        if nouvelle_pos > self.position:
            self.position = nouvelle_pos
            self.arrete = False
        else:
            self.arrete = True

    def au_point_de_virage(self):
        if self.direction == "droite" and self.position == self.POINT_DROITE:
            return True
        if self.direction == "gauche" and self.position == self.POINT_GAUCHE:
            return True
        return False

    def tourner(self):
        if self.direction == "droite":
            self.voie = self.VOIE_A_DROITE[self.voie]
            self.position = self.POINT_GAUCHE
        else:
            self.voie = self.VOIE_A_GAUCHE[self.voie]
            self.position = self.POINT_DROITE
        self.direction = "tout_droit"
        self.arrete = False

    def est_sortie(self):
        return self.position - self.LONGUEUR > self.FIN

    def dans_carrefour(self):
        if self.position <= self.LIGNE_ARRET:
            return False
        if self.position - self.LONGUEUR >= self.BORD_CARREFOUR:
            return False
        return True

    def rectangle(self):
        avant = self.position
        arriere = self.position - self.LONGUEUR
        if self.voie == "Nord":
            return [-35, arriere, self.LARGEUR, self.LONGUEUR]
        if self.voie == "Sud":
            return [15, -avant, self.LARGEUR, self.LONGUEUR]
        if self.voie == "Ouest":
            return [arriere, 15, self.LONGUEUR, self.LARGEUR]
        return [-avant, -35, self.LONGUEUR, self.LARGEUR]

    def touche(self, autre):
        r1 = self.rectangle()
        r2 = autre.rectangle()
        if r1[0] >= r2[0] + r2[2]:
            return False
        if r2[0] >= r1[0] + r1[2]:
            return False
        if r1[1] >= r2[1] + r2[3]:
            return False
        if r2[1] >= r1[1] + r1[3]:
            return False
        return True

    def to_dict(self):
        return {
            "id": self.identifiant,
            "voie": self.voie,
            "position": self.position,
            "longueur": self.LONGUEUR,
            "couleur": self.couleur,
            "urgence": self.urgence,
        }
