# Tests de la maquette

Depuis la racine du projet, dans l’environnement virtuel :

```bash
python -m unittest discover -s tests -v
```

Les tests vérifient le trajet selon la circulation, l’ordre de passage des urgences, l’annulation, les collisions dans des scénarios reproductibles et le mode adaptatif. Ils couvrent aussi la connexion TCP locale, les messages JSON fragmentés ou invalides, les confirmations du serveur, une panne d’écriture SQLite et les commandes de l’interface.

## Essai sur deux PC avant le rendu

1. Connecter le client Windows au serveur Debian avec [le guide de connexion](connexion.md).
2. Vérifier que les véhicules avancent et que les compteurs changent.
3. Demander une urgence avec une sortie sur le côté. Vérifier le trajet affiché et le feu bleu.
4. Demander une deuxième urgence. Vérifier le compteur de la file et le passage suivant.
5. Activer les feux adaptatifs et l’heure de pointe. Vérifier les confirmations du serveur.
6. Arrêter le serveur puis le redémarrer. Vérifier l’avertissement puis la reprise de l’affichage.

Noter la date, les deux systèmes utilisés et les résultats observés.
