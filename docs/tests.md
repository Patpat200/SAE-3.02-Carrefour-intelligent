# Vérifications du client

Depuis le dossier du projet, avec PyQt6 installé :

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Au 21 octobre 2026, les 11 tests passent :

- 7 tests de l'interface avec un client simulé : filtres, sélection, commandes,
  état observé, attente prolongée, déconnexion et données anciennes.
- 3 tests du protocole : messages fragmentés, caractères accentués, plusieurs
  messages dans une réception et JSON invalide.
- 1 test avec le vrai client et le vrai serveur sur `127.0.0.1`, un port libre
  et une base SQLite temporaire : connexion, déclenchement et fin d'urgence sur
  les quatre voies, puis vérification des événements enregistrés.

Le test local ne contacte pas le serveur du camarade et ne modifie pas la
configuration. Il nécessite de pouvoir ouvrir une socket locale et écrire
dans le dossier temporaire du système.

La fenêtre a aussi été vérifiée visuellement avec des données de démonstration :
table des véhicules, sélection et contour sur le dessin.

## Essai restant sur deux PC

1. Lancer le serveur sur Debian avec une écoute sur `0.0.0.0:5000`.
2. Renseigner son adresse IPv4 et le port dans l'onglet Connexion du client.
3. Vérifier l'arrivée continue des données et déclencher puis terminer une urgence.
4. Arrêter le serveur et vérifier l'avertissement, puis le redémarrer pour
   contrôler la reconnexion.

Les essais locaux ne valident pas le réseau Windows/Debian, le calcul d'un
itinéraire optimal ni les urgences simultanées.
