# Connexion au serveur

## Sur le même ordinateur

Dans l’environnement virtuel, lancer `python server_main.py` puis `python main.py` dans un autre terminal. Dans l’onglet **Réseau**, entrer `127.0.0.1` et le port `5000`.

## Sur deux ordinateurs

1. Sur le PC Debian, lancer `python3 server_main.py`. Le serveur écoute par défaut sur toutes ses interfaces au port TCP 5000.
2. Sur le serveur, utiliser `ip -4 -brief addr` pour trouver l’IPv4 de l’interface reliée au réseau des deux PC.
3. Depuis PowerShell sur Windows, essayer `Test-NetConnection <IP_DU_SERVEUR> -Port 5000`. Remplacer le texte entre chevrons par l’IPv4 trouvée.
4. Ouvrir le client. Dans l’onglet **Réseau**, saisir cette IPv4 et le port, puis cliquer sur **Se connecter / Réessayer**.

Si le port est inaccessible, vérifier l’adresse, le démarrage du serveur et les règles du pare-feu pour le port TCP 5000. Les préférences du client sont stockées dans `config/local_settings.json`. Le client réessaie automatiquement après une coupure. Le bouton **Se déconnecter** arrête ces tentatives.
