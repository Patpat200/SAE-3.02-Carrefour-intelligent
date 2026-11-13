from collections import deque

from .feu import Feu
from .pathfinder import Pathfinder
from .vehicle import Vehicule


def position_vehicule(vehicule):
    return vehicule.position


class Carrefour:
    VOIES = ("Nord", "Sud", "Est", "Ouest")
    TYPES_URGENCE = ("Secours", "Pompiers", "Police", "SAMU")
    MAX_URGENCES_EN_ATTENTE = 20

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
        self.phase_duree_vert = duree_vert
        self.strategie = "fixe"
        self.urgence_voie = None
        self.vehicule_prioritaire = None
        self.trajet_urgence = None
        self.urgences_en_attente = deque()

    def trouver_feu(self, voie):
        for feu in self.feux:
            if feu.nom == voie:
                return feu
        return None

    def tick(self):
        if self.urgence_voie is not None:
            return

        self.phase_compteur += 1
        duree = self.phase_duree_vert + self.feu_nord.duree_orange
        # on attend que le carrefour soit vide avant de changer de phase
        if self.phase_compteur >= duree and self.carrefour_libre():
            if self.phase == "NS":
                self.phase = "EW"
            else:
                self.phase = "NS"
            self.phase_compteur = 0
            self.phase_duree_vert = self.calculer_duree_vert()

        self.regler_phase()

    def calculer_duree_vert(self):
        duree_normale = self.feu_nord.duree_vert
        if self.strategie == "fixe":
            return duree_normale
        file_ns = self.compter_vehicules("Nord") + self.compter_vehicules("Sud")
        file_eo = self.compter_vehicules("Est") + self.compter_vehicules("Ouest")
        file_verte, file_rouge = (file_ns, file_eo) if self.phase == "NS" else (file_eo, file_ns)
        if file_verte == 0 and file_rouge > 0:
            return max(1, duree_normale // 2)
        if file_verte > file_rouge:
            return min(2 * duree_normale, duree_normale + file_verte)
        return duree_normale

    def regler_phase(self):
        if self.phase == "NS":
            voies_vertes = ("Nord", "Sud")
        else:
            voies_vertes = ("Est", "Ouest")

        duree_vert = self.phase_duree_vert
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

    def carrefour_libre(self):
        return not any(v.dans_carrefour() for v in self.vehicules)

    def calculer_trajet(self, depart, sortie):
        # Les liaisons en amont sont fictives. Passer par une autre entrée
        # coûte plus cher, mais peut éviter une file de voitures.
        arrivee = "Sortie " + sortie
        graphe = {"Départ": {}, arrivee: {}}
        for entree in self.VOIES:
            if entree == sortie:
                continue  # pas de demi-tour dans le carrefour
            noeud = "Entrée " + entree
            graphe["Départ"][noeud] = 2 if entree == depart else 8
            cout_traversee = 2 if Vehicule.VOIE_EN_FACE[entree] == sortie else 3
            # Chaque véhicule en approche rend cette entrée plus coûteuse.
            graphe[noeud] = {arrivee: cout_traversee + 2 * self.compter_vehicules(entree)}
        trajet = Pathfinder(graphe).trouver_trajet("Départ", arrivee)
        return trajet[1].split(" ", 1)[1]

    def declencher_urgence(self, voie, sortie=None, type_urgence="Secours"):
        if voie not in self.VOIES or (sortie is not None and sortie not in self.VOIES):
            raise ValueError("Voie ou sortie inconnue")
        if type_urgence not in self.TYPES_URGENCE:
            raise ValueError("Type de véhicule inconnu")

        demande = (voie, sortie, type_urgence)
        if self.vehicule_prioritaire is not None:
            if len(self.urgences_en_attente) >= self.MAX_URGENCES_EN_ATTENTE:
                raise ValueError("La file des urgences est pleine")
            self.urgences_en_attente.append(demande)
            return "Urgence ajoutée à la file d’attente"
        self.activer_urgence(*demande)
        return "Urgence prise en charge"

    def activer_urgence(self, depart, sortie, type_urgence):
        voie = depart
        if sortie is None:
            sortie = Vehicule.VOIE_EN_FACE[voie]
        else:
            voie = self.calculer_trajet(depart, sortie)
        self.urgence_voie = voie
        self.trajet_urgence = {
            "depart": depart, "entree": voie, "sortie": sortie, "type": type_urgence
        }

        for feu in self.feux:
            feu.etat = "ROUGE"
            feu.compteur = 0

        urgence = Vehicule(voie, urgence=True, type_urgence=type_urgence)
        # Les constantes de virage décrivent le sens de circulation en sortie.
        sens_sortie = Vehicule.VOIE_EN_FACE[sortie]
        if sens_sortie == Vehicule.VOIE_A_DROITE[voie]:
            urgence.direction = "droite"
        elif sens_sortie == Vehicule.VOIE_A_GAUCHE[voie]:
            urgence.direction = "gauche"

        for v in self.vehicules:
            if v.voie == voie:
                derriere = v.position - Vehicule.LONGUEUR - Vehicule.ECART_MIN
                urgence.position = min(urgence.position, derriere)
        self.vehicules.append(urgence)
        self.vehicule_prioritaire = urgence
        self.gerer_urgence()

    def gerer_urgence(self):
        if self.vehicule_prioritaire.est_sortie():
            self.terminer_urgence()
            return

        feu = self.trouver_feu(self.urgence_voie)
        if feu.etat != "PRIORITAIRE" and self.carrefour_libre():
            feu.activer_prioritaire()

    def fin_urgence(self):
        urgence = self.vehicule_prioritaire
        if urgence is None:
            return "Aucune urgence active"
        if urgence.position > Vehicule.LIGNE_ARRET:
            return "Véhicule déjà engagé, la priorité se termine après son passage"

        self.vehicules.remove(urgence)
        self.terminer_urgence()
        return "Urgence annulée"

    def terminer_urgence(self):
        voie = self.urgence_voie
        self.urgence_voie = None
        self.vehicule_prioritaire = None
        self.trajet_urgence = None

        if self.urgences_en_attente:
            self.activer_urgence(*self.urgences_en_attente.popleft())
            return

        # Repartir de l’orange sur l’axe qui vient d’avoir la priorité.
        self.phase = "NS" if voie in ("Nord", "Sud") else "EW"
        self.phase_duree_vert = self.feu_nord.duree_vert
        self.phase_compteur = self.phase_duree_vert
        self.regler_phase()

    def ajouter_vehicule(self, voie):
        for v in self.vehicules:
            if v.voie == voie and v.position < Vehicule.DEPART + 50:
                return False
        self.vehicules.append(Vehicule(voie))
        return True

    def avancer_vehicules(self):
        # Un seul véhicule peut occuper la zone du croisement. Les feux
        # gardent leur cycle, mais les autres véhicules attendent à la ligne.
        carrefour_libre = self.carrefour_libre()
        for feu in self.feux:
            voitures = [v for v in self.vehicules if v.voie == feu.nom]
            voitures.sort(key=position_vehicule, reverse=True)

            devant = None
            for v in voitures:
                if v.virage:
                    v.virage -= 1
                v.avancer(feu, devant, passage_libre=carrefour_libre)
                if v.dans_carrefour():
                    carrefour_libre = False
                devant = v

        for v in self.vehicules:
            if v.au_point_de_virage():
                v.tourner()

        self.vehicules = [v for v in self.vehicules if not v.est_sortie()]
        if self.vehicule_prioritaire is not None:
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
            "strategie": self.strategie,
            "trajet_urgence": self.trajet_urgence,
            "urgences_en_attente": len(self.urgences_en_attente),
        }

    def compter_vehicules(self, voie):
        nombre = 0
        for vehicule in self.vehicules:
            if vehicule.voie == voie and vehicule.position <= Vehicule.LIGNE_ARRET:
                nombre += 1
        return nombre
