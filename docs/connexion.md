# Connexion au serveur du binôme

Le client lit l'adresse et le port dans `config/settings.json`, section `network`.
L'adresse actuelle est `10.128.238.241` et le port est `5000`.

Sur le PC du camarade, lancer le serveur :

```powershell
python server_main.py
```

Son serveur écoute sur `0.0.0.0:5000`. Sur le PC client, depuis SAE2, lancer :

```powershell
.\venv\Scripts\python.exe main.py
```

Le client reçoit des messages JSON UTF-8 terminés par un retour à la ligne,
avec `type: state` et un dictionnaire `payload`. La connexion tourne dans
un thread séparé. La fenêtre lit le dernier état reçu toutes les 50 ms.
Si la connexion est perdue, le client retente selon `reconnect_delay_s`.

Le serveur fourni gère `trigger_emergency` et `clear_emergency`.
Les commandes d'heure de pointe et de stratégie restent désactivées tant que
le serveur ne transmet pas les champs `trafic` et `strategie` correspondants.

Si l'adresse IP du camarade change, mettre à jour `network.host` et relancer
le client. L'adresse doit être celle de son PC, pas `127.0.0.1`.

Pour vérifier l'accès au port depuis le client :

```powershell
Test-NetConnection 10.128.238.241 -Port 5000
```

`TcpTestSucceeded : True` confirme l'accès TCP. Si le résultat est faux,
vérifier que le serveur est lancé, que l'IP et le port sont corrects et que
le pare-feu du PC serveur autorise le port TCP 5000 sur le réseau utilisé.
Il n'est pas nécessaire de désactiver le pare-feu.

Les erreurs reçues sont affichées dans le panneau de connexion, la barre
inférieure ou l'historique. Fermer la fenêtre arrête le client réseau.
