# Installation

Python 3.11 ou supérieur et PyQt6 sont nécessaires.

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

Dans `config/settings.json`, renseigner l'adresse IP et le port du serveur.
Le serveur est développé et lancé séparément par le camarade.
Sans serveur connecté, seul le carrefour vide est affiché au démarrage.
