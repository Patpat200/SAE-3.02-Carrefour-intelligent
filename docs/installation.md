# Installation de la maquette

Cloner le dépôt et se placer dans son dossier.

```bash
git clone https://github.com/Patpat200/SAE-3.02-Carrefour-intelligent.git
cd SAE-3.02-Carrefour-intelligent
```

[Créer l’environnement virtuel et démarrer les deux programmes](../README.md#installer-et-lancer).

Le serveur utilise Python standard et SQLite. Le client a aussi besoin de PyQt6, installé à partir de `requirements.txt`. Le serveur se lance avec `python server_main.py` et le client avec `python main.py`, depuis la racine du dépôt.

Pour un essai sur un seul PC, saisir `127.0.0.1` et `5000` dans l’onglet **Réseau**. Sur deux machines, utiliser [le guide de connexion](connexion.md).
