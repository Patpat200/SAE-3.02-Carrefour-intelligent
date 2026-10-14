# Carrefour Connecté - Simulation de véhicules prioritaires

**SAE A3.09 (Développement Python) / SAE A3.02 (Gestion de projet & cahier des charges)**
**BUT R&T DevCloud - IUT de Colmar**
Binôme : Hussain AL SHAQSI & Adil EL BOUMAKHLOUFI

---

## Objectif

Aujourd'hui, un véhicule prioritaire (pompiers, police, SAMU) traverse un carrefour à la sirène, à la discrétion des autres automobilistes — un processus risqué et imprévisible qui peut coûter des vies.

Ce projet développe une **simulation en Python d'un carrefour connecté** capable de :

- **Recevoir** le signal d'urgence émis par un véhicule prioritaire
- **Calculer** dynamiquement son trajet optimal vers/à travers le carrefour
- **Basculer** automatiquement les feux concernés en mode « passage prioritaire »
- **Visualiser** graphiquement la simulation en temps réel (maquette)
- **Analyser** et afficher la densité du trafic aux intersections
- **Identifier** les véhicules d'urgence

Détail complet de la problématique, du périmètre fonctionnel (méthode MoSCoW) et du planning : voir le **cahier des charges** (`docs/reponse.md`).

---

## Fonctionnalités (périmètre MoSCoW)

| Fonctionnalité | Priorité |
|---|---|
| Réception et décodage du signal d'urgence | **Must have** |
| Calcul du trajet optimal vers le carrefour | **Must have** |
| Basculement automatique des feux en mode prioritaire | **Must have** |
| Simulation graphique du carrefour en temps réel (maquette) | **Must have** |
| Affichage de la densité de trafic aux intersections | Should have |
| Identification des véhicules d'urgence | Should have |
| Gestion de plusieurs véhicules prioritaires simultanés | Should have |
| Journalisation des événements (logs) | Could have |
| Interface de configuration (paramètres du carrefour) | Could have |
| Intégration avec une API cartographique externe | ❌ Won't have |

---

## Architecture

Architecture : **client-serveur**, avec un serveur qui gère l'état du carrefour, la simulation et les décisions de feux, et un client PyQt6 qui affiche l'interface graphique. Communication par **Sockets TCP (JSON ligne par ligne)**, concurrence par **Threads**.

---

## Réseau

Le code réseau est dans `src/network/`.

- **Serveur** (`server.py`) : il fait tourner la simulation et écoute sur `network.host` / `network.port` (par défaut `127.0.0.1:8765`). Il accepte plusieurs clients, avec un thread par client et un thread pour la simulation.
- **Client** (`client.py`) : il se connecte au serveur dans un thread séparé pour ne pas bloquer l'interface. Si la connexion est perdue, il réessaie tout seul toutes les `network.reconnect_delay_s` secondes.
- **Protocole** (`protocol.py`) : chaque message est un objet JSON encodé en UTF-8 et terminé par un retour à la ligne.

### Messages envoyés par le serveur

L'état complet du carrefour est envoyé à tous les clients à chaque déplacement des véhicules (toutes les 30 ms par défaut) :

```json
{"type": "state", "payload": {"feux": [], "vehicules": [], "densite": {}, "urgence": null, "strategie": "fixe", "trafic": {}}}
```

En cas de commande incorrecte, le serveur répond au client concerné :

```json
{"type": "error", "message": "Commande inconnue"}
```

### Commandes envoyées par le client

| Action | Exemple | Effet |
|---|---|---|
| `trigger_emergency` | `{"type": "command", "action": "trigger_emergency", "road": "Nord"}` | Déclenche une urgence sur la voie donnée |
| `clear_emergency` | `{"type": "command", "action": "clear_emergency"}` | Termine l'urgence en cours |
| `set_rush_hour` | `{"type": "command", "action": "set_rush_hour", "value": true}` | Active ou désactive le mode heure de pointe |
| `set_strategy` | `{"type": "command", "action": "set_strategy", "value": "adaptatif"}` | Choisit les feux `fixe` ou `adaptatif` |

Pour utiliser deux machines, mettre l'adresse IP du serveur dans `network.host` sur les deux postes (ou `0.0.0.0` côté serveur pour écouter sur toutes les interfaces).

---

## Fonctionnement de la simulation

### Carrefour modélisé
La maquette représente un carrefour qui existe vraiment à **Colmar** : le croisement de l'**Avenue d'Alsace (D 201)**, du nord au sud, et de la **Route de Neuf-Brisach (D 418)**, d'est en ouest. C'est le carrefour à feux qui mène vers le campus de l'université.

Le dessin reprend le terre-plein central avec des arbres et les bandes cyclables de l'avenue, les passages piétons, et les directions (Mulhouse au sud, Neuf-Brisach et Freiburg à l'est, le centre-ville à l'ouest). C'est une version simplifiée : une seule voie par sens, et les bâtiments autour sont décoratifs. Les noms affichés se changent en haut de `src/ui/carrefour_widget.py`.

### Feux
Les deux axes (Nord/Sud et Est/Ouest) passent au vert chacun leur tour : vert, orange, puis rouge. L'autre axe ne passe au vert que lorsque le carrefour est vide.

### Véhicules
- Des voitures apparaissent au hasard sur les quatre voies.
- Chaque voiture va tout droit, tourne à droite ou tourne à gauche.
- Pour tourner à gauche, une voiture attend au milieu du carrefour que celles d'en face soient passées.
- La voiture qui suit attend en retrait pour ne pas bloquer le milieu du carrefour, et une voiture qui tourne à droite ne coupe pas la route à celle qui arrive.
- Une voiture freine si une autre est en train de croiser sa route.
- Une voiture qui va tourner met son clignotant, et elle pivote progressivement pendant le virage.

### Véhicule prioritaire
- Il est rouge avec un contour jaune, une bande blanche et un gyrophare bleu qui clignote.
- Il se déclenche avec les boutons **Urgence Nord / Sud / Est / Ouest** du panneau de contrôle.
- Les voitures qui sont juste devant lui sur sa voie serrent à droite pour le laisser passer : avant le carrefour elles s'arrêtent sur le côté, après le carrefour elles continuent en roulant sur le bord. Une voiture déjà engagée dans le carrefour ou en plein virage termine d'abord sa manœuvre. Le véhicule d'urgence se décale vers le milieu pour les doubler, puis elles reprennent leur place.
- Tous les feux passent tout de suite au rouge, puis la voie du véhicule passe en mode prioritaire (feu bleu) dès que le carrefour est vide.
- Le cycle normal reprend tout seul quand le véhicule est sorti, ou avec le bouton **Fin urgence**.

### Mode heure de pointe
Par défaut, le trafic est constant. Le bouton **Activer l'heure de pointe** lance une journée simulée en accéléré (une journée dure 12 minutes par défaut) :
- le trafic est faible la nuit et monte jusqu'à 2,2 fois la normale vers 8h et 17h ;
- le matin, 75 % des voitures arrivent par l'Avenue d'Alsace (nord-sud) ; le soir, 75 % arrivent par la Route de Neuf-Brisach (est-ouest).

L'heure simulée et le niveau de trafic sont affichés dans le panneau.

### Deux stratégies de feux
Le bouton **Feux : fixes / adaptatifs** change de stratégie pendant la simulation :
- **Feux fixes** : chaque axe a toujours la même durée de vert.
- **Feux adaptatifs** : le vert s'arrête plus tôt quand plus personne n'arrive sur l'axe au vert et que des voitures attendent sur l'autre, et il est prolongé (jusqu'au double) quand il y a plus de voitures du côté vert que du côté rouge.

### Comparaison des deux stratégies
Le script `comparer_strategies.py` simule plusieurs journées avec heures de pointe, une fois avec les feux fixes et une fois avec les feux adaptatifs, avec exactement les mêmes voitures. Il affiche un tableau et enregistre le graphique `docs/comparaison_strategies.png`. Il se lance sans le serveur :

```bash
python comparer_strategies.py
```

![Comparaison des stratégies](docs/comparaison_strategies.png)

Sur 5 journées simulées, l'attente moyenne par véhicule passe de 31,0 s avec les feux fixes à 9,5 s avec les feux adaptatifs (environ 69 % de moins), et la plus longue file de 90 à 36 véhicules.

Plus de détails dans `docs/usage.md`.

---

## Configuration

Tout se règle dans `config/settings.json` :

| Paramètre | Rôle |
|---|---|
| `simulation.tick_ms` | Durée d'un cycle des feux (ms) |
| `simulation.vehicle_tick_ms` | Intervalle de déplacement des véhicules (ms) |
| `simulation.spawn_tick_ms` | Intervalle d'apparition des voitures (ms) |
| `network.host` / `network.port` | Adresse et port du serveur |
| `network.reconnect_delay_s` | Délai avant une nouvelle tentative de connexion du client |
| `feux.duree_vert_s` / `feux.duree_orange_s` | Durée du vert et de l'orange (secondes) |
| `feux.strategie` | Stratégie au démarrage : `fixe` ou `adaptatif` |
| `trafic.heure_de_pointe` | Démarre directement en mode heure de pointe |
| `trafic.minutes_par_seconde` | Vitesse de l'horloge simulée (2 = une journée en 12 minutes) |
| `logging.path` | Fichier SQLite des événements |

---

## Installation

### Prérequis
- Python 3.11+
- pip

### Mise en place

```bash
git clone https://github.com/Patpat200/SAE-3.02-Carrefour-intelligent.git
cd SAE-3.02-Carrefour-intelligent
python -m venv venv
source venv/bin/activate      # Linux / WSL2
venv\Scripts\activate         # Windows (cmd)
pip install -r requirements.txt
```

### Lancement

1) Démarrer le serveur :

```bash
python server.py
```

2) Démarrer le client graphique :

```bash
python main.py
```

Le serveur doit rester ouvert pendant l'utilisation du client. Le client peut
être lancé sur une autre machine en remplaçant `network.host` par l'adresse IP
de la machine qui héberge le serveur. Les événements d'urgence sont enregistrés
dans `logs/events.sqlite3`. Le serveur s'arrête avec `Ctrl+C`.

---

## Structure du projet

```
carrefour-connecte/
├── main.py                      # Point d'entrée du client graphique
├── comparer_strategies.py       # Compare feux fixes et adaptatifs (graphique)
├── server.py                    # Point d'entrée du serveur
├── requirements.txt             # Dépendances Python
├── Dockerfile                   # Image Docker (bonus)
├── docker-compose.yml           # Compose pour dev local (bonus)
├── run.sh                       # Script de lancement rapide (bonus)
├── README.md                    # Guide + explication du projet
│
├── .github/
│   └── workflows/
│       └── docker-publish.yml   # CI/CD → build & push sur ghcr.io
│
├── config/
│   └── settings.json            # Paramètres de simulation
│
├── src/
│   ├── core/                    # Logique métier (sans PyQt)
│   │   ├── carrefour.py         # Feux, urgence et virages
│   │   ├── feu.py               # Machine à états des feux
│   │   ├── vehicle.py           # Objet véhicule (déplacement, virage)
│   │   ├── simulateur.py        # Boucle de simulation
│   │   ├── trafic.py            # Arrivée des voitures, mode heure de pointe
│   │   └── pathfinder.py        # Algorithme de trajet optimal
│   │
│   ├── network/                 # Communication client-serveur (sockets TCP)
│   │   ├── server.py            # Serveur de simulation
│   │   ├── client.py            # Client réseau utilisé par l'interface
│   │   └── protocol.py          # Encodage / décodage des messages JSON
│   │
│   ├── ui/                      # Interface graphique PyQt6
│   │   ├── main_window.py       # Fenêtre principale
│   │   ├── carrefour_widget.py  # Dessin du carrefour et des véhicules
│   │   ├── vehicle_widget.py    # Couleur des véhicules
│   │   └── control_panel.py     # Panneau de contrôle
│   │
│   └── utils/
│       ├── logger.py            # Logs (SQLite)
│       └── config_loader.py     # Lecture de settings.json
├── logs/                        # Créé automatiquement au lancement du serveur
│
├── tests/                       # Tests unitaires
├── docs/
│   ├── installation.md
│   ├── usage.md                 # Guide d'utilisation
│   ├── comparaison_strategies.png  # Graphique produit par comparer_strategies.py
│   └── reponse.md               # Cahier des charges
│
└── assets/icons/
```

---

## Bonus : lancer avec Docker

Le projet n'exige pas Docker (non demandé par le cahier des charges) — c'est juste pratique pour tester la maquette sans installer Python/PyQt en local. L'image est construite automatiquement sur GitHub à chaque nouvelle version.

### Linux

```bash
xhost +local:docker

docker run --rm \
  -e DISPLAY=$DISPLAY \
  -e QT_QPA_PLATFORM=xcb \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --network host \
  ghcr.io/patpat200/sae-3.02-carrefour-intelligent:latest

xhost -local:docker
```

### Windows (WSLg / WSL2)

Ouvrir un terminal **WSL2**, puis la même chose :

```bash
xhost +local:docker

docker run --rm \
  -e DISPLAY=$DISPLAY \
  -e QT_QPA_PLATFORM=xcb \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --network host \
  ghcr.io/patpat200/sae-3.02-carrefour-intelligent:latest

xhost -local:docker
```

> **WSLg** (Windows 11 / Windows 10 récent) expose automatiquement un serveur X11 — pas besoin d'installer Xming ou VcXsrv.

### Script tout-en-un (Linux & WSL2)

```bash
chmod +x run.sh
./run.sh
```

### Build Docker local

```bash
docker compose up --build
```

### Publier une nouvelle version

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions build automatiquement l'image et la pousse sur `ghcr.io`.

---

## Jalons

| Date | Livrable |
|------|----------|
| 29/09/2026 | Cahier des charges validé |
| 15/11/2026 | Maquette fonctionnelle - `v0.1.0` |
| Juin 2027 | Simulation complète - `v1.0.0` |

---

Développé avec ♡ par le groupe Les étranger du Shawarme 68
