# CONTEXT.md - Comprendre le projet en 5 minutes

> Ce fichier est destiné à toute personne (humaine ou IA) qui rejoint le projet ou veut contribuer.
> Il répond aux questions : **c'est quoi, pourquoi, comment ça marche, par où commencer.**
>
> Ce projet suit le **cahier des charges** de la SAE A3.02 (`docs/reponse.md`), qui reste la référence en cas de doute sur le périmètre ou les priorités.

---

## C'est quoi ce projet ?

Une **simulation graphique en Python** d'un carrefour intelligent qui détecte les véhicules d'urgence (pompiers, police, SAMU) et bascule automatiquement les feux tricolores pour leur laisser le passage — en toute sécurité et le plus vite possible.

Le projet est réalisé dans le cadre d'une **SAE universitaire** (Situation d'Apprentissage et d'Évaluation) en BUT Réseaux et Télécommunications, spécialité DevCloud, à l'IUT de Colmar.

---

## Le problème que ça résout

Aujourd'hui, quand une ambulance ou un camion de pompiers traverse un carrefour, les feux ne s'adaptent pas. Le conducteur doit forcer le passage à la sirène, en espérant que les autres voitures s'écartent. C'est **risqué, imprévisible, et potentiellement fatal**.

Ce projet simule un système où :
1. Le véhicule prioritaire envoie un signal
2. Le carrefour reçoit le signal
3. Les feux passent automatiquement au vert sur sa trajectoire
4. Les autres voies sont bloquées le temps du passage

---

## Périmètre fonctionnel (MoSCoW — voir cahier des charges §3)

| Fonctionnalité | Priorité |
|---|---|
| Réception et décodage du signal d'urgence | Must have |
| Calcul du trajet optimal vers le carrefour | Must have |
| Basculement automatique des feux en mode prioritaire | Must have |
| Simulation graphique du carrefour en temps réel (maquette) | Must have |
| Affichage de la densité de trafic aux intersections | Should have |
| Gestion de plusieurs véhicules prioritaires simultanés | Should have |
| Journalisation des événements (logs) | Could have |
| Interface de configuration (paramètres du carrefour) | Could have |
| Intégration avec une API cartographique externe | Won't have |

Les « Could have » ne sont traités que si le temps restant le permet (budget ≤ 75h/étudiant, cf. cahier des charges §3).

---

## Qui travaille dessus ?

| Rôle | Nom | GitHub/Pseudo |
|------|-----|---------------|
| Développeur | Adil EL BOUMAKHLOUFI | `Patpat200` |
| Développeur | Hussain AL SHAQSI | `AL SHAQSI` |
| Enseignant référent | — | `fdrablin-uha` |

---

## Où en est le projet ?

| Jalon | Date | Statut |
|-------|------|--------|
| Cahier des charges | 29/09/2026 | ✅ Rédigé |
| Maquette fonctionnelle | 15/11/2026 | 🔲 En cours |
| Simulation complète | Juin 2027 | 🔲 À venir |

**Phase actuelle : maquette.** L'objectif immédiat est d'avoir une interface graphique PyQt6 qui affiche un carrefour, des feux qui changent d'état, et un véhicule prioritaire qui traverse.

---

## Architecture du code

Le cahier des charges (§2.2) définit une architecture **client-serveur** à terme : serveur pour l'état du carrefour et le calcul des trajets, client pour l'interface graphique, le tout relié par Sockets et Threads.

Pour la **maquette (phase 1)**, le projet reste **tout-en-un (standalone PyQt6)** — pas de serveur séparé, afin de livrer vite une démo fonctionnelle. La séparation client/serveur est prévue pour la **simulation complète (phase 2)**.

### Les deux grandes parties

```
src/core/   →  la logique, sans aucun import PyQt
src/ui/     →  l'affichage PyQt6, qui lit le core
```

Cette séparation est volontaire : on peut tester toute la logique (feux, véhicules, algorithmes) sans jamais lancer de fenêtre graphique — et elle prépare la bascule vers le client/serveur de la phase 2.

### Les fichiers clés à connaître

| Fichier | Rôle |
|---------|------|
| `main.py` | Point d'entrée — lance la fenêtre Qt |
| `src/core/feu.py` | Machine à états d'un feu : VERT → ORANGE → ROUGE → PRIORITAIRE |
| `src/core/carrefour.py` | État global du carrefour : 4 voies, liste de feux, position des véhicules |
| `src/core/vehicle.py` | Objet véhicule : type (pompiers/police/SAMU), position, vitesse |
| `src/core/simulateur.py` | Boucle principale : avance le temps tick par tick, met à jour feux et véhicules |
| `src/core/pathfinder.py` | Calcule le trajet optimal du véhicule prioritaire vers/à travers le carrefour |
| `src/ui/main_window.py` | Fenêtre Qt principale — assemble les widgets |
| `src/ui/carrefour_widget.py` | Dessin du carrefour et des feux (QPainter) |
| `src/ui/control_panel.py` | Boutons : déclencher un véhicule prioritaire, pause, vitesse |
| `config/settings.json` | Tous les paramètres configurables (durée des feux, vitesse simu, taille fenêtre) |

---

## Stack technique

| Technologie | Usage | Pourquoi |
|-------------|-------|----------|
| **Python 3.11+** | Langage principal | Imposé par la SAE |
| **PyQt6** | Interface graphique | Imposé par le cours (bibliothèque Qt) |
| **threading** | Concurrence | Boucle de simulation sans bloquer l'UI |
| **socket** | Communication réseau | Prévu pour la phase 2 (client/serveur) |
| **SQLite** | Logs des événements | Léger, embarqué, pas de serveur DB à gérer |
| **Git / GitHub** | Versioning | Dépôt partagé avec l'enseignant |
| **Docker** *(bonus, non requis par le cahier des charges)* | Déploiement facultatif | Image auto-publiée sur ghcr.io via GitHub Actions, pratique pour tester sans installer Python |

---

## Comment fonctionne la simulation

```
main.py
  └── lance MainWindow (Qt)
        ├── instancie Simulateur
        │     ├── contient un Carrefour (4 feux, voies)
        │     ├── fait avancer le temps (tick toutes les 500ms par défaut)
        │     └── appelle Pathfinder si un véhicule prioritaire est détecté
        └── affiche CarrefourWidget (redessine à chaque tick)
```

**Le cycle d'un tick :**
1. `Simulateur.tick()` est appelé par un `QTimer`
2. Chaque `Feu` avance son compteur (vert → orange → rouge)
3. Si un véhicule prioritaire est actif, `Pathfinder` calcule sa voie
4. Les feux sur sa trajectoire passent en mode `PRIORITAIRE`
5. `CarrefourWidget` se redessine pour refléter le nouvel état

---

## Conventions de code

- **PEP 8** — nommage snake_case, classes en PascalCase
- **Docstrings** sur toutes les classes et méthodes publiques
- **Pas d'import PyQt dans `src/core/`** — le core doit rester testable sans Qt
- **Tests dans `tests/`** — un fichier par module core
- **Logs** via `src/utils/logger.py` uniquement, pas de `print()` en prod

---

## Par où commencer si tu rejoins le projet

1. **Lire ce fichier**
2. **Lire le cahier des charges** (`docs/reponse.md`) pour le périmètre exact
3. **Lire le README.md** pour installer et lancer
4. **Commencer par `src/core/feu.py`** — c'est la brique la plus simple, tout le reste en dépend
5. **Puis `src/core/carrefour.py`** — il agrège les feux et les voies
6. **Puis `src/core/simulateur.py`** — il fait tourner le tout
7. **L'UI en dernier** — elle ne fait qu'afficher ce que le core calcule

---

## Questions fréquentes

**Pourquoi PyQt6 et pas Tkinter ?**
Imposé par le cours (module Paddoven). PyQt6 est plus puissant pour dessiner avec QPainter.

**Pourquoi pas de serveur séparé pour la maquette ?**
La maquette doit tourner entièrement en local, sans configuration réseau. Le client/serveur (sockets) arrive en phase 2 pour la simulation complète, conformément au cahier des charges §2.2.

**C'est quoi le `QTimer` dans la simu ?**
Un timer Qt qui appelle `simulateur.tick()` toutes les N millisecondes (configurable dans `settings.json`). Il tourne dans le thread principal Qt, ce qui évite les problèmes de concurrence pour la maquette.

**Le `pathfinder.py`, c'est quel algo ?**
À définir — probablement un algorithme de plus court chemin simple (Dijkstra ou BFS sur un graphe de voies) pour trouver quelle voie le véhicule va emprunter et quels feux doivent passer en prioritaire.

**Docker est obligatoire ?**
Non. Ce n'est pas demandé par le cahier des charges — c'est juste un moyen pratique de tester la maquette sans installer Python. Le chemin principal reste `venv` + `pip install -r requirements.txt` (voir README.md).

---

*Dernière mise à jour : 22/09/2026 — Adil EL BOUMAKHLOUFI*
