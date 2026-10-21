# Réponse au cahier des charges

## Projet de carrefour connecté pour véhicules prioritaires

**SAE A3.09 / A3.02 — BUT R&T DevCloud, IUT de Colmar**  
**Binôme : Hussain AL SHAQSI et Adil EL BOUMAKHLOUFI**  
**Point d'avancement : 21 octobre 2026**

Ce document répond au cahier des charges V2.1 du 16 septembre 2026. Il présente la solution retenue et l'avancement de la partie interface graphique dans ce dossier. La connexion TCP est intégrée. Les essais locaux passent ; le fonctionnement entre les deux PC reste à valider.

## 1. Contexte et objectif

Le projet consiste à simuler un carrefour capable de donner la priorité aux véhicules d'urgence : pompiers, police et SAMU. Le système doit recevoir une demande de passage, adapter les feux et permettre de suivre la situation à l'écran.

Nous avons choisi de représenter le croisement de l'Avenue d'Alsace et de la Route de Neuf-Brisach à Colmar. Le dessin constitue une maquette du carrefour, avec quatre voies, des feux, des passages piétons et des véhicules.

L'objectif est une démonstration logicielle. La sécurité d'un déploiement sur un véritable carrefour ne peut pas être validée par cette maquette.

## 2. Répartition entre le client et le serveur

Nous répartissons le développement en deux parties.

| Partie | Responsabilité |
|---|---|
| Interface graphique | Dessin du carrefour, affichage des véhicules et des feux, boutons, informations de trafic et historique visible |
| Serveur | Déplacement des véhicules, gestion des urgences, calcul des trajets, décisions sur les feux et calcul de la densité |
| Intégration commune | Format des données, raccordement réseau et essais de fonctionnement entre les deux parties |

Le client affiche les résultats du serveur. Il ne décide pas de la trajectoire des véhicules ni du moment où un feu change de couleur. L'affichage des virages utilise les informations de position et de progression fournies dans les données.

## 3. Choix techniques

Nous utilisons Python 3.11 ou supérieur, avec PyQt6 pour l'interface, conformément au cahier des charges. Les composants Qt servent à créer la fenêtre, les onglets, les boutons et le tableau des voies. Le carrefour est dessiné avec `QPainter`.

Un `QTimer` rafraîchit le dessin pour les gyrophares et les clignotants. Ce rafraîchissement ne fait pas avancer la simulation.

La configuration est lue dans `config/settings.json`. Les dépendances sont indiquées dans `requirements.txt` et l'application peut être lancée dans un environnement virtuel Python.

La communication utilise des sockets TCP et des messages JSON séparés par des retours à la ligne. Le client réseau fonctionne dans un thread séparé pour éviter de bloquer la fenêtre. Les boutons transmettent des demandes et `afficher_etat` présente les données reçues du serveur.

Le serveur possède une journalisation SQLite, vérifiée lors du test local. L'historique de l'interface reste en mémoire, limité à 100 événements, avec un export en texte.

## 4. Réponse aux exigences fonctionnelles

| Exigence du cahier des charges | Priorité | Réponse et état actuel |
|---|---|---|
| Réception et décodage du signal d'urgence | Must have | Commandes TCP disponibles ; déclenchement et fin d'urgence testés avec le serveur local. |
| Calcul du trajet optimal | Must have | Module présent côté serveur, mais raccordement à la simulation et validation encore nécessaires. Aucun calcul de trajet dans l'interface. |
| Basculement automatique des feux | Must have | Décision côté serveur. L'interface affiche les états reçus, dont le passage prioritaire en bleu. |
| Simulation graphique en temps réel | Must have | Réception et affichage des états disponibles ; essai entre les deux PC restant à réaliser. |
| Affichage de la densité du trafic | Should have | Tableau affichant le nombre de véhicules fourni pour chaque voie. |
| Plusieurs véhicules prioritaires simultanés | Should have | À réaliser : une nouvelle urgence remplace actuellement la précédente. |
| Journalisation des événements | Could have | Historique horodaté et exportable ; journalisation SQLite côté serveur testée en local. |
| Interface de configuration | Could have | Adresse et port configurables dans l'interface et enregistrés en JSON. Configuration complète du carrefour à compléter. |
| API cartographique externe | Won't have | Non intégrée, conformément au périmètre retenu. |

## 5. Interface réalisée

La fenêtre affiche le carrefour à gauche et un panneau organisé en cinq onglets à droite.

- **Suivi** : tableau des quatre voies, couleurs des feux, urgence active, heure simulée, niveau de trafic et stratégie reçue.
- **Véhicules** : liste filtrable par voie ou urgence ; sélectionner une ligne repère le véhicule sur le dessin sans changer son mouvement.
- **Connexion** : adresse, port, connexion et déconnexion volontaires.
- **Commandes** : demandes d'urgence par direction, fin d'urgence, activation de l'heure de pointe et choix des feux fixes ou adaptatifs.
- **Historique** : demandes effectuées et changements reçus, avec leur heure, effacement et export en texte.

Le dessin comprend les routes, les trottoirs, les passages piétons, les bâtiments, un parc, des panneaux et les noms des rues. Une case permet de masquer les bâtiments et le parc. Le dessin s'adapte à la taille de la fenêtre.

Les commandes sont désactivées tant que l'interface n'est pas déclarée connectée. Un clic prépare une demande et attend les nouvelles données du serveur ; il ne modifie pas directement les feux ou le trafic. Les commandes de trafic et de stratégie restent désactivées si le serveur ne fournit pas les informations correspondantes. Une absence de données pendant trois secondes est signalée. Après une demande, le message distingue « envoyée » et « état observé », avec un avertissement après cinq secondes. Le protocole ne fournit pas d'accusé de réception identifié par commande ; observer un état ne prouve donc pas quelle commande l'a produit.

## 6. Vérifications réalisées

Les 11 tests automatisés passent : 7 tests de l'interface avec un client simulé, 3 tests du décodage du protocole et 1 test avec le vrai client et le vrai serveur en local. Ce dernier vérifie le déclenchement et la fin d'urgence sur les quatre voies ainsi que les événements SQLite.

La liste des véhicules, sa sélection et le contour sur le dessin ont également été vérifiés visuellement. Les instructions figurent dans `docs/tests.md`. Ces essais ne valident pas le réseau entre Windows et Debian, le calcul de trajet ni la sécurité des transitions des feux.

## 7. Organisation et prochaines étapes

Le cahier des charges estime le travail à environ 84 heures pour le binôme, hors révisions et tests, avec une limite de 75 heures par étudiant. Cette estimation ne constitue pas un relevé des heures réellement effectuées.

La priorité est de valider la communication entre les deux PC, puis de raccorder le calcul de trajet et de traiter les urgences simultanées côté serveur. Les transitions des feux restent également à tester.

| Échéance prévue | Livrable |
|---|---|
| 15 novembre 2026 | Maquette fonctionnelle avec communication entre le client et le serveur |
| Décembre 2026 à mai 2027 | Compléments, tests et corrections de la simulation |
| Juin 2027, si le projet est sélectionné | Simulation complète et documentation |

Les fonctionnalités obligatoires passent avant les ajouts facultatifs. La gestion de plusieurs urgences, les tests sur deux machines et les transitions des feux restent à traiter ou à vérifier avec le développement serveur.

## 8. Bilan actuel

La partie graphique permet de recevoir, afficher et filtrer les données du serveur, puis d'envoyer les commandes. La séparation des responsabilités est conservée : le serveur gère la simulation et le client présente son état. L'achèvement dépend encore des fonctions serveur et des essais communs. Un pourcentage précis nécessite une grille de validation partagée du cahier des charges.
