import random
import unittest
from itertools import combinations

from src.core.carrefour import Carrefour
from src.core.vehicle import Vehicule


class CarrefourTests(unittest.TestCase):
    def test_trajet_change_selon_la_file(self):
        carrefour = Carrefour()
        self.assertEqual(carrefour.calculer_trajet("Nord", "Sud"), "Nord")
        for _ in range(5):
            carrefour.vehicules.append(Vehicule("Nord"))

        carrefour.declencher_urgence("Nord", "Sud", "Pompiers")
        vehicule = carrefour.vehicule_prioritaire
        self.assertNotEqual(vehicule.voie, "Nord")
        self.assertEqual(vehicule.type_urgence, "Pompiers")
        self.assertIn(vehicule.direction, ("gauche", "droite"))
        for _ in range(500):
            carrefour.avancer_vehicules()
            if vehicule.est_sortie():
                break
        self.assertTrue(vehicule.est_sortie())
        self.assertEqual(vehicule.voie, Vehicule.VOIE_EN_FACE["Sud"])

    def test_file_et_annulation_urgence(self):
        carrefour = Carrefour()
        carrefour.declencher_urgence("Nord")
        premiere = carrefour.vehicule_prioritaire
        carrefour.declencher_urgence("Est", "Ouest", "SAMU")
        self.assertIs(carrefour.vehicule_prioritaire, premiere)
        self.assertEqual(carrefour.get_state()["urgences_en_attente"], 1)
        self.assertIn("annulée", carrefour.fin_urgence())
        self.assertNotIn(premiere, carrefour.vehicules)
        self.assertEqual(carrefour.vehicule_prioritaire.type_urgence, "SAMU")
        seconde = carrefour.vehicule_prioritaire
        seconde.position = Vehicule.LIGNE_ARRET + 1
        self.assertIn("déjà engagé", carrefour.fin_urgence())
        self.assertIs(carrefour.vehicule_prioritaire, seconde)

    def test_pas_de_chevauchement_avec_trafic_et_urgences(self):
        etat_random = random.getstate()
        self.addCleanup(random.setstate, etat_random)
        for graine in range(5):
            random.seed(graine)
            carrefour = Carrefour({"duree_vert_s": 10, "duree_orange_s": 4})
            for tick in range(1500):
                if tick % 17 == 0:
                    carrefour.tick()
                if tick % 40 == 0:
                    carrefour.ajouter_vehicule(random.choice(Carrefour.VOIES))
                if tick == 250:
                    carrefour.declencher_urgence("Nord", "Est", "Police")
                if tick == 275:
                    carrefour.declencher_urgence("Est", "Ouest", "SAMU")

                carrefour.avancer_vehicules()
                for a, b in combinations(carrefour.vehicules, 2):
                    self.assertFalse(a.touche(b), (graine, tick, a.voie, b.voie))

            self.assertIsNone(carrefour.urgence_voie)
            self.assertFalse(carrefour.urgences_en_attente)

    def test_strategie_adaptative_change_la_duree(self):
        carrefour = Carrefour()
        carrefour.strategie = "adaptatif"
        carrefour.ajouter_vehicule("Nord")
        self.assertGreater(carrefour.calculer_duree_vert(), carrefour.feu_nord.duree_vert)
        carrefour.phase = "EW"
        self.assertLess(carrefour.calculer_duree_vert(), carrefour.feu_nord.duree_vert)
