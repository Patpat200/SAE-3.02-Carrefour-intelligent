from .feu import Feu
from .vehicle import Vehicule


def position_vehicule(vehicule):
    return vehicule.position


class Carrefour:
    VOIES = ("Nord", "Sud", "Est", "Ouest")

    def __init__(self, feux_settings=None):
        if feux_settings is None:
            feux_settings = {}
        duree_vert = feux_settings.get("duree_vert_s", 10)
        duree_orange = feux_settings.get("duree_orange_s", 3)
        duree_rouge = feux_settings.get("duree_rouge_s", 13)

        self.feu_nord = Feu("Nord", duree_vert, duree_orange, duree_rouge)
        self.feu_sud = Feu("Sud", duree_vert, duree_orange, duree_rouge)
        self.feu_est = Feu("Est", duree_vert, duree_orange, duree_rouge)
        self.feu_ouest = Feu("Ouest", duree_vert, duree_orange, duree_rouge)

        self.feux = [self.feu_nord, self.feu_sud, self.feu_est, self.feu_ouest]

        self.feu_nord.etat = "VERT"
        self.feu_sud.etat = "VERT"
        self.feu_est.etat = "ROUGE"
        self.feu_ouest.etat = "ROUGE"

        self.vehicules = []
        self.phase = "NS"
        self.phase_compteur = 0
        self.urgence_voie = None

    def trouver_feu(self, voie):
        for feu in self.feux:
            if feu.nom == voie:
                return feu
        return None

    def tick(self):
        if self.urgence_voie is not None:
            return

        self.phase_compteur += 1
        duree = self.feu_nord.duree_vert + self.feu_nord.duree_orange
        # on attend que le carrefour soit vide avant de changer de phase
        if self.phase_compteur >= duree and self.carrefour_libre(None):
            if self.phase == "NS":
                self.phase = "EW"
            else:
                self.phase = "NS"
            self.phase_compteur = 0

        self.regler_phase()

    def regler_phase(self):
        if self.phase == "NS":
            voies_vertes = ("Nord", "Sud")
        else:
            voies_vertes = ("Est", "Ouest")

        duree_vert = self.feu_nord.duree_vert
        duree_orange = self.feu_nord.duree_orange
        compteur = self.phase_compteur

        for feu in self.feux:
            if feu.nom not in voies_vertes:
                feu.etat = "ROUGE"
                feu.compteur = 0
            elif compteur < duree_vert:
                feu.etat = "VERT"
                feu.compteur = compteur
            elif compteur < duree_vert + duree_orange:
                feu.etat = "ORANGE"
                feu.compteur = compteur - duree_vert
            else:
                feu.etat = "ROUGE"
                feu.compteur = 0

    def carrefour_libre(self, voie_autorisee):
        for v in self.vehicules:
            if v.dans_carrefour() and v.origine != voie_autorisee:
                return False
        return True

    def declencher_urgence(self, voie_urgente):
        self.urgence_voie = voie_urgente

        for feu in self.feux:
            if feu.nom != voie_urgente or feu.etat != "PRIORITAIRE":
                feu.etat = "ROUGE"
                feu.compteur = 0

        anciens = self.vehicules
        self.vehicules = []
        for v in anciens:
            if not v.urgence:
                self.vehicules.append(v)

        urgence = Vehicule(voie_urgente, urgence=True)
        for v in self.vehicules:
            if v.voie == voie_urgente:
                derriere = v.position - Vehicule.LONGUEUR - Vehicule.ECART_MIN
                if derriere < urgence.position:
                    urgence.position = derriere
        self.vehicules.append(urgence)

        self.gerer_urgence()

    def gerer_urgence(self):
        urgence_presente = False
        for v in self.vehicules:
            if v.urgence:
                urgence_presente = True

        if not urgence_presente:
            self.fin_urgence()
            return

        feu = self.trouver_feu(self.urgence_voie)
        if feu.etat != "PRIORITAIRE" and self.carrefour_libre(self.urgence_voie):
            feu.activer_prioritaire()

    def fin_urgence(self):
        if self.urgence_voie is None:
            return
        # le cycle reprend à l'orange sur l'axe de l'urgence
        if self.urgence_voie == "Nord" or self.urgence_voie == "Sud":
            self.phase = "NS"
        else:
            self.phase = "EW"
        self.phase_compteur = self.feu_nord.duree_vert
        self.urgence_voie = None
        for feu in self.feux:
            feu.desactiver_prioritaire()
        self.regler_phase()

    def ajouter_vehicule(self, voie):
        for v in self.vehicules:
            if v.voie == voie and v.position < Vehicule.DEPART + 50:
                return False
        self.vehicules.append(Vehicule(voie))
        return True

    def peut_tourner(self, vehicule):
        if vehicule.direction == "droite":
            nouvelle_voie = Vehicule.VOIE_A_DROITE[vehicule.voie]
            nouvelle_pos = Vehicule.POINT_GAUCHE
        else:
            nouvelle_voie = Vehicule.VOIE_A_GAUCHE[vehicule.voie]
            nouvelle_pos = Vehicule.POINT_DROITE
        en_face = Vehicule.VOIE_EN_FACE[vehicule.voie]
        feu_en_face = self.trouver_feu(en_face)
        place = Vehicule.LONGUEUR + Vehicule.ECART_MIN

        for autre in self.vehicules:
            if autre is vehicule:
                continue
            if autre.voie == nouvelle_voie:
                if abs(autre.position - nouvelle_pos) < place:
                    return False
            # pour tourner à gauche on laisse passer ceux d'en face
            if vehicule.direction == "gauche" and autre.voie == en_face:
                if not autre.arrete and autre.position < 20:
                    if autre.position > Vehicule.LIGNE_ARRET:
                        return False
                    if feu_en_face.etat == "VERT" or feu_en_face.etat == "PRIORITAIRE":
                        return False
        return True

    def est_bloque(self, vehicule):
        # bloqué par la voiture de devant qui vient de tourner
        for autre in self.vehicules:
            if autre.voie != vehicule.voie and autre.origine == vehicule.origine:
                if vehicule.touche(autre):
                    return True
        return False

    def avancer_vehicules(self):
        for feu in self.feux:
            voitures = []
            for v in self.vehicules:
                if v.voie == feu.nom:
                    voitures.append(v)
            voitures.sort(key=position_vehicule, reverse=True)

            devant = None
            for v in voitures:
                ancienne_pos = v.position
                deja_bloque = self.est_bloque(v)
                v.avancer(feu, devant)
                if not deja_bloque and self.est_bloque(v):
                    v.position = ancienne_pos
                    v.arrete = True
                devant = v

        for v in self.vehicules:
            if v.au_point_de_virage() and self.peut_tourner(v):
                v.tourner()

        restants = []
        for v in self.vehicules:
            if not v.est_sortie():
                restants.append(v)
        self.vehicules = restants

        if self.urgence_voie is not None:
            self.gerer_urgence()

    def get_state(self):
        feux = []
        for feu in self.feux:
            feux.append(feu.to_dict())

        vehicules = []
        for vehicule in self.vehicules:
            vehicules.append(vehicule.to_dict())

        densite = {}
        for voie in self.VOIES:
            densite[voie] = self.compter_vehicules(voie)

        return {
            "feux": feux,
            "vehicules": vehicules,
            "densite": densite,
            "urgence": self.urgence_voie,
        }

    def compter_vehicules(self, voie):
        nombre = 0
        for vehicule in self.vehicules:
            if vehicule.voie == voie:
                nombre += 1
        return nombre
