# Carrefour connecté - Client graphique

Interface Python avec PyQt6 pour le projet SAE.

Le client dessine le carrefour, les feux et les voitures à partir des données
reçues du serveur. Les boutons envoient des demandes d'urgence au serveur.
Le déplacement, les feux, les priorités et le calcul du trafic sont gérés
par le serveur développé par l'autre membre du binôme.

## Lancement

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

Sans serveur, la fenêtre reste ouverte avec le carrefour vide et les boutons
désactivés. La connexion est retentée automatiquement. Après une déconnexion,
le dernier état reçu reste visible avec le statut déconnecté.

## Fichiers

- `main.py` : lancement.
- `src/ui/main_window.py` : réception des données et mise à jour de l'interface.
- `src/ui/carrefour_widget.py` : dessin du carrefour.
- `src/ui/control_panel.py` : boutons, connexion et trafic.
- `src/ui/vehicle_widget.py` : couleur des véhicules.
- `src/network/client.py` : connexion TCP dans un thread.
- `src/network/protocol.py` : messages JSON.
- `config/settings.json` : adresse du serveur et taille de la fenêtre.

## Communication avec le serveur

L'adresse par défaut est `127.0.0.1:8765`. Modifier `network.host` si le serveur
est sur le PC du camarade. Chaque message est un objet JSON UTF-8 terminé par
un retour à la ligne.

Exemple d'état reçu :

```json
{"type":"state","payload":{"feux":[{"nom":"Nord","etat":"VERT"}],"vehicules":[{"voie":"Nord","position":-120,"longueur":28,"couleur":"blue","urgence":false}],"densite":{"Nord":1,"Sud":0,"Est":0,"Ouest":0},"urgence":null}}
```

Le serveur transmet les quatre feux et tous les véhicules. Les états des feux
sont `VERT`, `ORANGE`, `ROUGE` ou `PRIORITAIRE`. Les voies sont `Nord`, `Sud`,
`Est` et `Ouest`. La position représente l'avant du véhicule par rapport au
centre du carrefour, négative avant le centre et positive après.

Commandes envoyées :

```json
{"type":"command","action":"trigger_emergency","road":"Nord"}
{"type":"command","action":"clear_emergency"}
```

Un clic ne change pas directement les feux ou les voitures : le client attend
le nouvel état envoyé par le serveur.
