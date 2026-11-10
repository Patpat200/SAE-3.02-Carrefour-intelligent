# Réponse au cahier des charges

**SAÉ A3.09 / A3.02 · BUT R&T DevCloud, IUT de Colmar**
Adil EL BOUMAKHLOUFI et Hussain AL SHAQSI

La maquette simule le croisement de l’avenue d’Alsace et de la route de Neuf-Brisach. Le serveur gère la circulation et la priorité. Le client graphique montre ses décisions en temps réel.

| Exigence V2.1 | Priorité | Réalisation |
|---|---|---|
| Réception du signal d’urgence | Obligatoire | Une commande TCP simulée indique le départ, la sortie et le type. Les pompiers, la police et le SAMU sont distingués. |
| Calcul du trajet optimal | Obligatoire | Dijkstra choisit une entrée sur un graphe simulé dont les coûts varient avec le nombre de véhicules en approche. La trajectoire choisie est utilisée par le véhicule et affichée. |
| Basculement automatique des feux | Obligatoire | Le serveur ferme les accès, attend que le centre se libère et ouvre l’entrée choisie en mode prioritaire. |
| Affichage graphique en temps réel | Obligatoire | Le client PyQt6 affiche les états reçus par TCP et suit les véhicules. |
| Densité du trafic | Souhaité | Le panneau affiche un compteur de véhicules en approche pour chacune des quatre entrées. |
| Plusieurs demandes prioritaires | Souhaité | La file conserve plusieurs demandes et les traite dans l’ordre d’arrivée. Un véhicule prioritaire traverse à la fois. |
| Journalisation | Facultatif | SQLite conserve les commandes traitées. La fenêtre propose aussi un historique exportable. |
| Configuration | Facultatif | Le client permet de modifier l’adresse, le port et certains réglages en direct. Le fichier JSON permet de modifier les durées et les intervalles serveur. |
| API cartographique | Hors périmètre | Le graphe et les coûts sont simulés. |

Le trajet est optimal selon les coûts définis dans la maquette. Les liaisons du graphe ne représentent pas des itinéraires routiers réels. Le passage d’un seul véhicule à la fois simplifie la gestion des conflits au centre.

## Validation du rendu

L’essai automatisé local est décrit dans [docs/tests.md](tests.md). Pour la remise de la maquette le 15 novembre 2026, il reste à consigner l’essai de bout en bout entre les deux PC du binôme. Le cahier des charges prévoit aussi des comptes rendus hebdomadaires d’une page maximum, à compléter à partir du travail réellement effectué.
