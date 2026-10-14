class Pathfinder:
    def __init__(self):
        self.graph = {
            "Nord": {"Sud": 2, "Est": 1, "Ouest": 1},
            "Sud": {"Nord": 2, "Est": 1, "Ouest": 1},
            "Est": {"Nord": 1, "Sud": 1, "Ouest": 2},
            "Ouest": {"Nord": 1, "Sud": 1, "Est": 2},
        }

    def trouver_trajet(self, depart, arrivee):
        if depart not in self.graph or arrivee not in self.graph:
            raise ValueError("Voie inconnue")

        distances = {}
        for voie in self.graph:
            distances[voie] = 999999
        distances[depart] = 0
        precedents = {}
        a_visiter = list(self.graph.keys())

        while len(a_visiter) > 0:
            voie = a_visiter[0]
            for autre in a_visiter:
                if distances[autre] < distances[voie]:
                    voie = autre
            a_visiter.remove(voie)

            if voie == arrivee:
                break

            for suivante in self.graph[voie]:
                nouvelle_distance = distances[voie] + self.graph[voie][suivante]
                if nouvelle_distance < distances[suivante]:
                    distances[suivante] = nouvelle_distance
                    precedents[suivante] = voie

        trajet = [arrivee]
        while trajet[-1] != depart:
            trajet.append(precedents[trajet[-1]])
        trajet.reverse()
        return trajet


def calculer_trajet_optimal(depart, arrivee):
    pathfinder = Pathfinder()
    return pathfinder.trouver_trajet(depart, arrivee)
