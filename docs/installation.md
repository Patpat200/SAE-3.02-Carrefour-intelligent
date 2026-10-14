# Guide d'installation

## Prérequis système
- Python 3.11 ou supérieur
- pip (inclus avec Python)
- Git

## Étapes

### 1. Cloner le dépôt
```bash
git clone https://github.com/<votre-repo>/carrefour-connecte.git
cd carrefour-connecte
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel
**Windows :**
```bash
venv\Scripts\activate
```
**Linux / macOS :**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Lancer le serveur puis le client
```bash
python server.py
```

Dans un second terminal :
```bash
python main.py
```

Docker n'est pas nécessaire pour cette version. Le dossier `logs` est créé
automatiquement par le serveur.