# Comprendre le code de la maquette

## De la fenêtre au serveur

`main.py` lance la fenêtre PyQt6. Quand on clique sur un bouton d’urgence, `MainWindow` donne à `NetworkClient` le point de départ, la sortie demandée et le type du véhicule. Le client envoie une commande en TCP. Le serveur traite la commande et renvoie un résultat avec le même identifiant. « Urgence ajoutée à la file d’attente » signifie que la demande a été enregistrée et attend son tour.

Le serveur envoie aussi des états successifs. Le thread réseau du client lit ces états. Un timer Qt les récupère dans le thread graphique pour actualiser le dessin et les tableaux.

Un message est un objet JSON en UTF-8 terminé par un saut de ligne. Un `recv` peut contenir un bout de message ou plusieurs messages. Le tampon de `protocol.py` conserve les morceaux jusqu’à la ligne suivante. Le serveur rejette un JSON mal formé ou trop long et nettoie la connexion concernée.

## Choisir le trajet

`Carrefour.calculer_trajet` construit un petit graphe. Il relie le départ du véhicule aux entrées possibles, puis les entrées à la sortie demandée. Les chemins en amont sont fictifs. L’entrée du même côté que le départ coûte 2. Passer par une autre entrée coûte 8. La traversée coûte 2 en ligne droite ou 3 en tournant, plus 2 par véhicule en approche.

`Pathfinder` applique Dijkstra pour trouver le chemin le moins coûteux. Par exemple, de Nord vers Sud, avec cinq véhicules en approche au Nord, le coût direct vaut `2 + 2 + 5 × 2 = 14`. Une entrée Est ou Ouest libre peut donner un coût de `8 + 3 = 11`. Le véhicule emprunte alors cette entrée et tourne vers le Sud.

Les commandes anciennes qui indiquent uniquement la voie gardent le trajet direct. L’interface actuelle envoie toujours une sortie.

## Éviter les collisions

Les deux axes alternent vert, orange et rouge. Au moment d’ouvrir un autre axe, le serveur attend que le véhicule engagé ait dégagé la zone centrale. Même avec un feu vert, un véhicule attend à la ligne si le centre est occupé. Une voiture sur la même voie garde aussi un écart avec celle de devant.

À l’arrivée d’une urgence, tous les feux passent au rouge. Le feu de l’entrée choisie devient bleu quand le centre est libre. Les voitures déjà devant le véhicule prioritaire peuvent dégager la voie. Les demandes suivantes patientent dans une file FIFO et l’itinéraire est calculé à leur activation avec la circulation du moment.

L’annulation retire le véhicule s’il est encore avant la ligne ou sur la ligne. S’il est déjà engagé, il termine son passage. La file continue ensuite dans l’ordre d’arrivée.

## Trafic, configuration et journal

Le nombre affiché par entrée inclut les véhicules qui approchent ou attendent à la ligne. En mode adaptatif, le serveur compare les deux axes au début de chaque phase. Il adapte la durée du vert avant de lancer la phase. En heure de pointe, le serveur fait apparaître davantage de véhicules le matin et en fin d’après-midi. Une journée simulée dure douze minutes.

Le fichier `config/settings.json` permet de régler les durées, les intervalles de simulation et le port du serveur. Les préférences personnelles du client sont dans un fichier local séparé.

Le verrou du carrefour protège les données partagées entre les threads. Le serveur écrit dans SQLite après avoir relâché le verrou. Si la base est indisponible, le serveur signale l’erreur et la simulation continue. L’historique de la fenêtre est séparé et peut être exporté en texte.
