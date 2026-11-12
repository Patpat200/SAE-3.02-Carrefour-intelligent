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

**Debian**

```bash
sudo apt update && apt upgrade
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
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python server_main.py
```

Dans un deuxième terminal, depuis la racine du projet, lancez le client.

```powershell
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
main.py
```

**Debian**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server_main.py # NE SOURTOUT PAS ETRE EN ROOT NI SUDO NI EN SU -
```

Dans un deuxième terminal, depuis la racine du projet, lancez le client.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py # NE SOURTOUT PAS ETRE EN ROOT NI SUDO NI EN SU -
```

Sur la VM cliente, une fois l’interface graphique lancée, ouvrez l’onglet **Réseau** et renseignez l’adresse IP de la VM serveur. Pour connaître cette adresse, exécutez `hostname -I` sur la VM serveur.













### 1. Installer Docker (optionnel)

#### Windows avec Docker Desktop

1. Si WSL est absent, ouvrez PowerShell en administrateur et lancez `wsl --install`. Redémarrez Windows si demandé. Pour mettre à jour WSL, lancez `wsl --update`.
2. Téléchargez [Docker Desktop pour Windows](https://docs.docker.com/desktop/setup/install/windows-install/). Installez-le avec le moteur WSL 2 et ouvrez Docker Desktop.
3. Une fois le moteur démarré, ouvrez PowerShell et vérifiez l’installation.

```powershell
docker version
docker compose version
```

#### Linux avec les paquets de la distribution

**Debian 13**

```bash
sudo apt update && upgrade
sudo apt install docker.io docker-compose
```

**Debian 12** fournit Compose v1 dans ses dépôts standard. Pour utiliser les commandes `docker compose` de ce guide, installez Docker Engine et `docker-compose-plugin` depuis le dépôt officiel. [Guide Docker pour Debian](https://docs.docker.com/engine/install/debian/#install-using-the-apt-repository)

Démarrez Docker et vérifiez Compose.

```bash
sudo systemctl enable --now docker
sudo docker compose version
```

### 2. Récupérer le fichier Compose

Téléchargez `compose.yaml` depuis la racine du dépôt s’il est disponible. Sinon, créez un dossier et enregistrez-y ce contenu dans un fichier nommé exactement `compose.yaml`.

```yaml
services:
  carrefour:
    image: ghcr.io/patpat200/sae-3.02-carrefour-intelligent:latest
    ports:
      - "0.0.0.0:5000:5000"
    volumes:
      - carrefour-logs:/app/logs

volumes:
  carrefour-logs:
```

### 3. Démarrer le serveur

Ouvrez un terminal dans le dossier de `compose.yaml`. Docker télécharge l’image au premier lancement. Le volume `carrefour-logs` conserve la base SQLite.

**Windows**

```powershell
docker compose up -d
docker compose ps
```

**Debian**

```bash
sudo docker compose up -d
sudo docker compose ps
```

Pour consulter les messages du serveur, lancez `docker compose logs carrefour`. Pour arrêter le serveur, lancez `docker compose down`. Sous Linux, ajoutez `sudo` à ces commandes si vous utilisez Docker comme dans les exemples ci-dessus.


### 4. Ouvrir l’interface

Sur le PC qui affiche la maquette, [installez Python, pip et Git](#1-installer-python-pip-et-git), puis [clonez le projet](#2-cloner-le-projet). Ouvrez un terminal à la racine du dépôt cloné.

**Windows avec PowerShell**

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Debian ou Ubuntu**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py # NE SOURTOUT PAS ETRE EN ROOT NI SUDO NI EN SU -
```

- **Sur le même PC**, renseignez `127.0.0.1` et le port `5000` dans l’onglet **Réseau**.
- **Sur deux PC**, remplacez `127.0.0.1` dans `compose.yaml` par l’IPv4 locale de la machine Docker, par exemple `192.168.1.20:5000:5000`. Relancez `docker compose up -d`, puis saisissez cette même IPv4 et le port `5000` dans l’interface. Utilisez le réseau local pour ce test. [Publication des ports Docker](https://docs.docker.com/engine/network/port-publishing/)

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

Pour lancer les tests, utilisez `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` sous Windows ou `.venv/bin/python -m unittest discover -s tests -v` sous Linux. Les essais automatisés du réseau tournent en local. Le guide de test décrit l’essai séparé sur les deux PC du binôme.

- [Cahier des charges d’origine](docs/CahierDesCharges.docx)
- [Réponse au cahier des charges](docs/reponse.md)
- [Utilisation de l’interface](docs/usage-interface.md)
- [Explications du code](docs/explications.md)
- [Tests](docs/tests.md)
