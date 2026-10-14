import random

from .carrefour import Carrefour


class Simulateur:
    def __init__(self, carrefour=None):
        self.carrefour = carrefour or Carrefour()

    def tick(self):
        self.carrefour.tick()
        self.carrefour.avancer_vehicules()

    def ajouter_vehicule_aleatoire(self):
        return self.carrefour.ajouter_vehicule(random.choice(Carrefour.VOIES))

    def get_state(self):
        return self.carrefour.get_state()