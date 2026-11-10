# Utilisation de l'interface graphique

Lancer `main.py` dans l'environnement Python du projet.

## Connexion

Ouvrir l'onglet **Réseau**, renseigner l'adresse du PC serveur et son port,
puis cliquer sur **Se connecter / Réessayer**. Les paramètres sont enregistrés
dans `config/local_settings.json`. Une nouvelle tentative remet l'affichage des
véhicules à zéro en attendant les données du serveur sélectionné.

Le client retente automatiquement une connexion perdue. **Se déconnecter**
arrête ces tentatives et garde le dernier état à l'écran pour consultation.

Une connexion TCP ouverte ne garantit pas que les données arrivent encore :
après trois secondes sans nouvel état, un message signale que l'affichage n'est
plus actualisé. Les voitures affichées restent celles du dernier état reçu.

## Suivi et commandes

Le tableau de suivi présente les véhicules en approche et les états des feux. Dans **Actions**, choisir le type de véhicule et une sortie, puis cliquer sur le bouton correspondant à son point de départ. « En face » choisit la sortie opposée au départ. Le serveur peut choisir une autre entrée selon le trafic.

L’onglet **Suivi** indique le trajet actif et le nombre de demandes en attente. **Annuler l’urgence active** retire le véhicule s’il n’est pas encore engagé. Sinon, il finit son passage. Les demandes en attente sont traitées dans leur ordre d’arrivée.

La fenêtre affiche d’abord « Envoyée », puis le résultat transmis par le serveur. Après cinq secondes sans réponse, un avertissement apparaît. Une réponse tardive peut encore arriver. Le journal garde les réponses reçues et le panneau suit la dernière demande.

Les boutons de trafic permettent d’activer l’heure de pointe et de changer de stratégie de feux. La nouvelle durée de vert s’applique à la prochaine phase normale.

## Véhicules

L'onglet **Véhicules** liste les identifiants, les voies et les types reçus.
Choisir une voie ou cocher **Seulement les véhicules d'urgence** pour filtrer.
Le compteur indique combien de véhicules sont affichés parmi ceux reçus.

Sélectionner une ligne entoure le véhicule en rose sur le dessin. La sélection
reste active pendant ses déplacements et disparaît lorsqu'il quitte les données
reçues ou le filtre. Cette action ne change pas son trajet.

## Historique et capture

Dans **Journal**, cliquer sur **Exporter l'historique en texte** et choisir
un fichier. L'export contient les événements encore affichés, au maximum 100.
Le bouton d'effacement agit uniquement sur cet historique local.

Dans **Suivi**, **Enregistrer une capture du carrefour** crée une image PNG du
dessin, avec son indication d'actualisation. Cela ne modifie pas la simulation.

Les exports restent disponibles lorsque le serveur est déconnecté.

## Préférences de la fenêtre

La taille de la fenêtre, le dernier onglet ouvert et l'affichage du décor sont
enregistrés à la fermeture. Ils sont restaurés au prochain lancement. Ces
préférences appartiennent au client et ne modifient pas la simulation.
