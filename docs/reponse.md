# Réponse au cahier des charges

## Projet de carrefour connecté pour véhicules prioritaires

**SAE A3.09 / A3.02 — BUT R&T DevCloud, IUT de Colmar**  
**Binôme : Hussain AL SHAQSI et Adil EL BOUMAKHLOUFI**  
**Point d'avancement : 14 octobre 2026**

Ce document répond au cahier des charges V2.1 du 16 septembre 2026. Il présente la solution retenue et l'avancement de la partie interface graphique dans ce dossier. La connexion avec le serveur reste à intégrer avant de pouvoir présenter une simulation complète.

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

L'architecture cible utilise des sockets TCP et des messages JSON. La communication devra fonctionner dans un thread séparé pour éviter de bloquer la fenêtre. Dans cette version, la méthode `afficher_etat` reçoit les données à afficher et le signal `command_requested` expose les demandes des boutons. Ces points d'entrée sont prêts pour le raccordement, mais aucun client réseau n'est lancé par cette interface.

SQLite est prévu pour la journalisation persistante. L'historique actuel reste uniquement en mémoire et ne remplace pas cette base de données.

## 4. Réponse aux exigences fonctionnelles

| Exigence du cahier des charges | Priorité | Réponse et état actuel |
|---|---|---|
| Réception et décodage du signal d'urgence | Must have | Traitement à assurer côté serveur. Les demandes de l'interface sont préparées ; leur transmission réseau reste à intégrer. |
| Calcul du trajet optimal | Must have | Fonction côté serveur, à valider lors de l'intégration. Aucun calcul de trajet dans l'interface. |
| Basculement automatique des feux | Must have | Décision côté serveur. L'interface affiche les états reçus, dont le passage prioritaire en bleu. |
| Simulation graphique en temps réel | Must have | Dessin et mise à jour à partir de données disponibles. Le fonctionnement en temps réel avec le serveur reste à vérifier. |
| Affichage de la densité du trafic | Should have | Tableau affichant le nombre de véhicules fourni pour chaque voie. |
| Plusieurs véhicules prioritaires simultanés | Should have | Gestion complète à valider côté serveur. L'indicateur d'urgence actuel affiche une seule voie. |
| Journalisation des événements | Could have | Historique horodaté à l'écran, limité à 100 entrées. Enregistrement SQLite à réaliser. |
| Interface de configuration | Could have | Lecture d'un fichier JSON disponible. Aucun formulaire de configuration du carrefour pour le moment. |
| API cartographique externe | Won't have | Non intégrée, conformément au périmètre retenu. |

## 5. Interface réalisée

La fenêtre affiche le carrefour à gauche et un panneau organisé en trois onglets à droite.

- **Suivi** : tableau des quatre voies, couleurs des feux, urgence active, heure simulée, niveau de trafic et stratégie reçue.
- **Commandes** : demandes d'urgence par direction, fin d'urgence, activation de l'heure de pointe et choix des feux fixes ou adaptatifs.
- **Historique** : demandes effectuées et changements reçus, avec leur heure et un bouton pour effacer la liste.

Le dessin comprend les routes, les trottoirs, les passages piétons, les bâtiments, un parc, des panneaux et les noms des rues. Une case permet de masquer les bâtiments et le parc. Le dessin s'adapte à la taille de la fenêtre.

Les commandes sont désactivées tant que l'interface n'est pas déclarée connectée. Un clic prépare une demande et attend les nouvelles données du serveur ; il ne modifie pas directement les feux ou le trafic. L'heure de la dernière mise à jour reste affichée pour identifier les données anciennes.

## 6. Vérifications réalisées

Les vérifications ont porté sur l'ouverture de la fenêtre, le redimensionnement, les trois onglets, le tableau des voies, l'affichage des véhicules, des virages et des urgences, ainsi que les commandes préparées par les sept boutons.

Des données de test ont permis de vérifier que les boutons ne modifient pas l'état de la simulation. L'historique a également été vérifié : absence de répétition à chaque mise à jour identique, limite de 100 entrées et effacement de la liste.

Ces essais valident le comportement de l'interface avec des données de test. Ils ne valident pas encore la communication TCP, les calculs du serveur ni la sécurité des décisions de priorité.

## 7. Organisation et prochaines étapes

Le cahier des charges estime le travail à environ 84 heures pour le binôme, hors révisions et tests, avec une limite de 75 heures par étudiant. Cette estimation ne constitue pas un relevé des heures réellement effectuées.

La priorité est de raccorder le client et le serveur, puis de tester une demande d'urgence complète : clic dans l'interface, réception côté serveur, modification de l'état et retour des données vers l'affichage.

| Échéance prévue | Livrable |
|---|---|
| 15 novembre 2026 | Maquette fonctionnelle avec communication entre le client et le serveur |
| Décembre 2026 à mai 2027 | Compléments, tests et corrections de la simulation |
| Juin 2027, si le projet est sélectionné | Simulation complète et documentation |

Les fonctionnalités obligatoires passent avant les ajouts facultatifs. La gestion de plusieurs urgences, les tests sur deux machines et la journalisation persistante restent à traiter ou à vérifier avec le développement serveur.

## 8. Bilan actuel

La partie graphique permet déjà de représenter les données du carrefour et de préparer les commandes utilisateur. La séparation des responsabilités est conservée : le serveur gère la simulation et le client présente son état. La prochaine étape est l'intégration réseau, nécessaire pour démontrer le fonctionnement complet demandé dans le cahier des charges.
