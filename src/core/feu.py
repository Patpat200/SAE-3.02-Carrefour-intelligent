class Feu:
    def __init__(self, nom, duree_vert=10, duree_orange=3, duree_rouge=13):
        self.nom = nom
        self.etat = "ROUGE"
        self.compteur = 0
        self.duree_vert = duree_vert
        self.duree_orange = duree_orange
        self.duree_rouge = duree_rouge
        self.etat_precedent = None

    def tick(self):
        if self.etat == "PRIORITAIRE":
            return

        self.compteur += 1

        if self.etat == "ROUGE" and self.compteur >= self.duree_rouge:
            self.etat = "VERT"
            self.compteur = 0

        elif self.etat == "VERT" and self.compteur >= self.duree_vert:
            self.etat = "ORANGE"
            self.compteur = 0

        elif self.etat == "ORANGE" and self.compteur >= self.duree_orange:
            self.etat = "ROUGE"
            self.compteur = 0

    def activer_prioritaire(self):
        if self.etat != "PRIORITAIRE":
            self.etat_precedent = self.etat
            self.etat = "PRIORITAIRE"
            self.compteur = 0

    def desactiver_prioritaire(self):
        if self.etat == "PRIORITAIRE":
            self.etat = "ROUGE"
            self.compteur = 0

    def to_dict(self):
        return {
            "nom": self.nom,
            "etat": self.etat,
            "compteur": self.compteur,
        }