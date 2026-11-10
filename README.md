# Carrefour intelligent

**SAÉ A3.09 / A3.02 BUT Réseaux et Télécommunications, IUT de Colmar**
Adil EL BOUMAKHLOUFI et Hussain AL SHAQSI

La maquette représente le croisement de l’avenue d’Alsace et de la route de Neuf-Brisach à Colmar. Elle montre comment des feux peuvent donner la priorité aux véhicules de secours.

## Installer et lancer

### 1. Installer Python, pip et Git

Le projet demande **Python 3.11 ou plus récent**. `pip` sert à installer les bibliothèques du projet, dont PyQt6. Git sert à récupérer le code depuis GitHub.

**Windows avec PowerShell**

Installez le [gestionnaire d’installation Python](https://www.python.org/downloads/windows/) et [Git pour Windows](https://git-scm.com/install/windows). Ouvrez ensuite un nouveau terminal PowerShell. Si Python 3.15 est déjà installé, passez directement aux commandes de vérification.

```powershell
pymanager install 3.15
py -3.15 --version
py -3.15 -m pip --version
git --version
```

Pip est fourni avec Python. Si la commande affiche `No module named pip`, lancez `py -3.15 -m ensurepip --upgrade` et vérifiez à nouveau.

**Debian ou Ubuntu**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git

python3 --version
python3 -m pip --version
git --version
```

### 2. Cloner le projet

Dans le terminal, placez-vous dans le dossier où vous voulez ranger le projet. Les commandes sont les mêmes sous Windows et Linux.

```bash
git clone https://github.com/Patpat200/SAE-3.02-Carrefour-intelligent.git
cd SAE-3.02-Carrefour-intelligent
```

### 3. Installer les dépendances et lancer la maquette

L’environnement virtuel `.venv` garde les bibliothèques du projet dans son propre dossier. Les commandes ci-dessous utilisent directement son exécutable Python.

**Windows avec PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python server_main.py
```

Dans un deuxième terminal, depuis la racine du projet, lancez le client.

```powershell
python main.py
```

**Debian ou Ubuntu**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server_main.py
```

Dans un deuxième terminal, depuis la racine du projet, lancez le client.

```bash
.venv/bin/python main.py
```

Sur le même PC, utilisez **127.0.0.1** et le **port 5000** dans l’onglet **Réseau**. Sur deux PC, le client utilise l’adresse IPv4 du PC serveur. Gardez le serveur ouvert pendant la simulation. [Connexion sur deux PC](docs/connexion.md)

## Faire une démonstration

1. Dans **Actions**, choisissez le type de véhicule et la sortie. Le bouton **Urgence Nord**, par exemple, indique le point de départ côté Nord.
2. Dans **Suivi**, lisez l’entrée retenue et la sortie. Le serveur compare des chemins sur un graphe simplifié. Un détour peut coûter moins cher si beaucoup de véhicules attendent devant l’entrée directe.
3. Envoyez une deuxième demande avant la fin de la première. Elle entre dans la file d’attente. Le serveur les traite dans leur ordre d’arrivée.
4. Essayez l’heure de pointe et les feux adaptatifs. Le tableau compte les véhicules en approche. En mode adaptatif, le nombre de véhicules en approche peut raccourcir ou allonger le vert de la prochaine phase.
5. Dans **Véhicules**, sélectionnez une ligne pour repérer une voiture sur le dessin. Le **Journal** permet de relire et d’exporter les événements affichés.

La simulation autorise un seul véhicule à traverser le centre à la fois. Le feu bleu représente le passage prioritaire. Les liaisons en amont, les coûts d’itinéraire et les véhicules sont simulés.

## Où lire le code

| Fichier ou dossier | Rôle |
|---|---|
| `server_main.py` | Charge la configuration et lance le serveur |
| `main.py` | Lance l’interface PyQt6 |
| `src/core/` | Modèle du carrefour, véhicules, feux et calcul de trajet |
| `src/network/` | Échanges TCP avec des messages JSON terminés par un saut de ligne |
| `src/ui/` | Dessin, suivi et boutons |
| `config/settings.json` | Réglages partagés du serveur et valeurs initiales du client |
| `tests/` | Tests du modèle, du réseau et de l’interface |

L’interface enregistre ses préférences dans `config/local_settings.json`, ignoré par Git. Le journal SQLite du serveur se trouve par défaut dans `logs/events.sqlite3`.

## Vérifications et rendu

Lancer `python -m unittest discover -s tests -v` dans l’environnement virtuel. Les essais automatisés du réseau tournent en local. Le guide de test décrit l’essai séparé sur les deux PC du binôme.

- [Cahier des charges d’origine](docs/CahierDesCharges.docx)
- [Réponse au cahier des charges](docs/reponse.md)
- [Utilisation de l’interface](docs/usage-interface.md)
- [Explications du code](docs/explications.md)
- [Tests](docs/tests.md)
