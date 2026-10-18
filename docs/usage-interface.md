# Utilisation de l'interface graphique

Lancer `main.py` dans l'environnement Python du projet.

## Connexion

Ouvrir l'onglet **Connexion**, renseigner l'adresse du PC serveur et son port,
puis cliquer sur **Se connecter / Réessayer**. Les paramètres sont enregistrés
dans `config/settings.json`. Une nouvelle tentative remet l'affichage des
véhicules à zéro en attendant les données du serveur sélectionné.

Le client retente automatiquement une connexion perdue. **Se déconnecter**
arrête ces tentatives et garde le dernier état à l'écran pour consultation.

Une connexion TCP ouverte ne garantit pas que les données arrivent encore :
après trois secondes sans nouvel état, un message signale que l'affichage n'est
plus actualisé. Les voitures affichées restent celles du dernier état reçu.

## Suivi et commandes

Le tableau de suivi présente les nombres de véhicules et les états des feux
transmis par le serveur. Les demandes d'urgence sont dans l'onglet **Commandes**.
Les réglages d'heure de pointe et de stratégie restent désactivés lorsque le
serveur n'en fournit pas les données.

L'interface ne calcule pas les déplacements, les priorités ou les cycles des feux.

## Historique et capture

Dans **Historique**, cliquer sur **Exporter l'historique en texte** et choisir
un fichier. L'export contient les événements encore affichés, au maximum 100.
Le bouton d'effacement agit uniquement sur cet historique local.

Dans **Suivi**, **Enregistrer une capture du carrefour** crée une image PNG du
dessin, avec son indication d'actualisation. Cela ne modifie pas la simulation.

Les exports restent disponibles lorsque le serveur est déconnecté.
