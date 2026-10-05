# Utilisation

Lancer l'interface avec `python main.py` dans l'environnement virtuel.

Le carrefour est à gauche, les commandes et les informations à droite.
Les feux, les positions des voitures, le trafic et l'urgence affichée
proviennent du serveur.

- **Urgence Nord / Sud / Est / Ouest** envoie une demande au serveur.
- **Fin urgence** demande au serveur de terminer l'urgence.

Les boutons sont désactivés lorsque le client n'est pas connecté.
Le client ne calcule pas les déplacements ou les changements de feux.
La connexion est retentée automatiquement si le serveur est indisponible.
