# Explications du code

Ce document explique comment le projet fonctionne, pourquoi chaque choix a été
fait, et ce que fait chaque partie du code. Il sert à comprendre le projet en
entier et à préparer la soutenance.

Les extraits de code sont copiés depuis les fichiers. Les fonctions les plus
importantes sont expliquées ligne par ligne ; les fonctions très simples
(une ou deux lignes évidentes) sont expliquées en une phrase.

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Les grands choix](#2-les-grands-choix)
3. [Le repère : comment une voiture est placée](#3-le-repère--comment-une-voiture-est-placée)
4. [Le temps : les ticks](#4-le-temps--les-ticks)
5. [config/settings.json](#5-configsettingsjson)
6. [src/core/feu.py](#6-srccorefeupy)
7. [src/core/vehicle.py](#7-srccorevehiclepy)
8. [src/core/trafic.py](#8-srccoretraficpy)
9. [src/core/carrefour.py](#9-srccorecarrefourpy)
10. [src/network/protocol.py](#10-srcnetworkprotocolpy)
11. [src/network/server.py](#11-srcnetworkserverpy)
12. [src/network/client.py](#12-srcnetworkclientpy)
13. [src/ui (interface graphique)](#13-srcui-interface-graphique)
14. [src/utils](#14-srcutils)
15. [main.py et server.py](#15-mainpy-et-serverpy)
16. [Problèmes rencontrés et solutions](#16-problèmes-rencontrés-et-solutions)
17. [Limites et code non utilisé](#17-limites-et-code-non-utilisé)
18. [Questions possibles à la soutenance](#18-questions-possibles-à-la-soutenance)

---

## 1. Vue d'ensemble

Le projet est coupé en deux programmes :

- **le serveur** (`python server.py`) : il fait tourner la simulation. Il sait
  où sont les voitures, de quelle couleur sont les feux, s'il y a une urgence.
- **le client** (`python main.py`) : c'est la fenêtre. Il ne calcule rien, il
  dessine ce que le serveur lui envoie et il envoie les clics des boutons.

```
        CLIENT (main.py)                         SERVEUR (server.py)
 ┌───────────────────────────┐            ┌────────────────────────────┐
 │ MainWindow                │            │ SimulationServer           │
 │  ├─ CarrefourWidget       │   état     │  ├─ Carrefour              │
 │  │   (dessin)             │ ◄───────── │  │   ├─ 4 Feu              │
 │  ├─ ControlPanel          │  33x / s   │  │   ├─ liste de Vehicule  │
 │  │   (boutons)            │            │  │   └─ Trafic             │
 │  └─ NetworkClient         │ ─────────► │  └─ EventLogger (SQLite)   │
 └───────────────────────────┘ commandes  └────────────────────────────┘
                     socket TCP, messages JSON, une ligne par message
```

Les dossiers suivent ce découpage :

| Dossier | Rôle | Utilise PyQt ? |
|---|---|---|
| `src/core/` | La simulation (feux, voitures, trafic) | Non |
| `src/network/` | Les sockets (serveur, client, format des messages) | Non |
| `src/ui/` | La fenêtre et le dessin | Oui |
| `src/utils/` | Lecture de la config, journal des événements | Non |

---

## 2. Les grands choix

| Choix | Pourquoi |
|---|---|
| **Client-serveur** | Demandé par le sujet. Avantage : plusieurs fenêtres peuvent regarder la même simulation, même depuis une autre machine. |
| **Toute la logique côté serveur** | Tous les clients voient exactement la même chose. Le client ne peut pas tricher ni se désynchroniser. |
| **Sockets TCP** | TCP garantit que les messages arrivent, dans l'ordre. Avec UDP il aurait fallu gérer les pertes nous-mêmes. |
| **JSON, une ligne par message** | JSON est lisible et se convertit directement en dictionnaire Python. TCP est un flux continu sans séparation : le retour à la ligne sert à savoir où un message finit. |
| **Threads** | Le serveur doit faire trois choses en même temps : accepter les clients, écouter chaque client, faire avancer la simulation. Un thread par tâche est la solution la plus simple. |
| **Verrous (`Lock`)** | Deux threads touchent au carrefour (la simulation et les commandes des clients). Le verrou empêche qu'ils le modifient en même temps. |
| **PyQt6** | Bibliothèque graphique imposée. Le dessin est fait à la main avec `QPainter` (rectangles, cercles, texte). |
| **SQLite pour les logs** | Fourni avec Python, pas de serveur de base de données à installer. |
| **Un vrai carrefour comme modèle** | Avenue d'Alsace (D 201) / Route de Neuf-Brisach (D 418) à Colmar, vérifié sur OpenStreetMap. C'est plus parlant qu'une croix grise. |
| **Code volontairement simple** | Boucles `for`, `if`, listes et dictionnaires. Pas de syntaxe avancée, pour que tout le groupe puisse le lire et l'expliquer. |

---

## 3. Le repère : comment une voiture est placée

C'est **le point le plus important à comprendre**, tout le reste en dépend.

Une voiture n'a pas de coordonnées x et y. Elle a seulement :

- `voie` : la voie sur laquelle elle roule (`"Nord"`, `"Sud"`, `"Est"`, `"Ouest"`) ;
- `position` : un seul nombre, la position de **l'avant** de la voiture le long
  de sa voie. `0` est le centre du carrefour.

Le nom d'une voie est l'endroit **d'où la voiture vient**. Une voiture de la
voie `"Nord"` vient du nord et descend vers le sud.

```
position :  -180      -70    -50        0        +50              +300
              │        │      │         │         │                 │
           apparition  │   bord du   centre    bord du         disparition
                    ligne  carrefour          carrefour
                   d'arrêt
              ───────────────────► sens de circulation
```

Les voitures roulent à droite, comme en France. Chaque voie est une bande de
20 pixels de large, à 25 pixels du centre de la route :

| Voie | Elle roule vers | Sur l'écran |
|---|---|---|
| Nord | le bas | bande verticale à gauche du centre (x de -35 à -15) |
| Sud | le haut | bande verticale à droite du centre (x de 15 à 35) |
| Ouest | la droite | bande horizontale en bas du centre (y de 15 à 35) |
| Est | la gauche | bande horizontale en haut du centre (y de -35 à -15) |

**Pourquoi ce choix ?** Avec un seul nombre, faire avancer une voiture c'est
`position = position + vitesse`, quelle que soit sa direction. Le feu, la
voiture de devant, la ligne d'arrêt : tout se compare avec ce seul nombre.
C'est le client qui transforme `voie + position` en pixels au moment de
dessiner.

Les nombres importants (ce sont les constantes en haut de `vehicle.py`) :

| Constante | Valeur | Signification |
|---|---|---|
| `LONGUEUR` | 30 | longueur d'une voiture |
| `LARGEUR` | 20 | largeur d'une voiture |
| `DEPART` | -180 | position où une voiture apparaît |
| `FIN` | 300 | une voiture disparaît quand son arrière dépasse 300 |
| `LIGNE_ARRET` | -70 | ligne où on s'arrête au feu rouge |
| `BORD_CARREFOUR` | 50 | la route fait 100 de large, donc le carrefour va de -50 à +50 |
| `ECART_MIN` | 10 | espace minimum entre deux voitures |
| `POINT_DROITE` | -25 | position où on tourne à droite |
| `POINT_GAUCHE` | 25 | position où on tourne à gauche |
| `POINT_ATTENTE` | -35 | position où on attend en retrait sans gêner |
| `PATIENCE` | 70 | nombre de ticks maximum à freiner pour une voiture qui croise |
| `DUREE_VIRAGE` | 14 | nombre de ticks que dure l'animation d'un virage |
| `DECALAGE_VOITURE` | 13 | de combien une voiture se range sur le côté |
| `DECALAGE_URGENCE` | -11 | de combien le véhicule d'urgence se décale vers le milieu |
| `DISTANCE_SIRENE` | 160 | distance à laquelle on réagit au véhicule d'urgence |

---

## 4. Le temps : les ticks

Un **tick** est un petit pas de temps. Il y a deux horloges, réglées dans
`settings.json` :

| Horloge | Durée | Ce qui se passe |
|---|---|---|
| tick des feux (`tick_ms`) | 500 ms | `Carrefour.tick()` : les feux avancent d'un cran |
| tick des véhicules (`vehicle_tick_ms`) | 30 ms | `Carrefour.avancer_vehicules()` : les voitures bougent |

**Pourquoi deux horloges ?** Les voitures doivent bouger souvent pour que
l'animation soit fluide (33 fois par seconde). Les feux n'ont pas besoin de
cette précision : deux fois par seconde suffit.

Une voiture a une vitesse de 2 à 4 pixels par tick, soit environ 65 à 130
pixels par seconde.

Dans `settings.json`, les durées des feux sont en **secondes**. Le serveur les
convertit en **nombre de ticks de feux** : 30 s de vert / 0,5 s = 60 ticks.

---

## 5. config/settings.json

```json
"simulation": { "tick_ms": 500, "vehicle_tick_ms": 30, "spawn_tick_ms": 1200, "nb_voies": 4 }
```
- `tick_ms`, `vehicle_tick_ms` : les deux horloges vues au-dessus.
- `spawn_tick_ms` : en trafic normal, une voiture arrive toutes les 1,2 s.
- `nb_voies` : pas utilisé par le code (le carrefour a toujours 4 voies).

```json
"network": { "host": "127.0.0.1", "port": 8765, "reconnect_delay_s": 2 }
```
- `host`, `port` : adresse du serveur. `127.0.0.1` = la même machine.
- `reconnect_delay_s` : le client réessaie de se connecter toutes les 2 s.

```json
"feux": { "duree_vert_s": 30, "duree_orange_s": 3, "duree_rouge_s": 27, "strategie": "fixe" }
```
- `duree_vert_s`, `duree_orange_s` : durée du vert et de l'orange.
- `duree_rouge_s` : lu mais pas utilisé. Le rouge d'un axe dure simplement le
  temps du vert et de l'orange de l'autre axe.
- `strategie` : `"fixe"` ou `"adaptatif"` au démarrage.

```json
"trafic": { "heure_de_pointe": false, "minutes_par_seconde": 2 }
```
- `heure_de_pointe` : démarrer directement en mode heure de pointe.
- `minutes_par_seconde` : vitesse de l'horloge simulée. Avec 2, une heure
  simulée dure 30 s et une journée 12 minutes.

```json
"logging": { "path": "logs/events.sqlite3" }
```
- fichier où le serveur enregistre les événements.

```json
"carrefour": { "largeur_px": 600, "hauteur_px": 600 }
```
- pas utilisé par le code (le dessin s'adapte à la taille de la fenêtre).

---

## 6. src/core/feu.py

Un objet `Feu` représente un seul feu.

```python
def __init__(self, nom, duree_vert=10, duree_orange=3, duree_rouge=13):
    self.nom = nom                  # "Nord", "Sud", "Est" ou "Ouest"
    self.etat = "ROUGE"             # "VERT", "ORANGE", "ROUGE" ou "PRIORITAIRE"
    self.compteur = 0               # depuis combien de ticks il est dans cet état
    self.duree_vert = duree_vert    # durées en ticks
    self.duree_orange = duree_orange
    self.duree_rouge = duree_rouge
    self.etat_precedent = None      # état avant le passage en prioritaire
```

L'état `"PRIORITAIRE"` est un quatrième état ajouté pour l'urgence. Pour les
voitures, il se comporte comme un vert. Il est dessiné en bleu pour qu'on voie
à l'écran que ce n'est pas un vert normal.

- `activer_prioritaire()` : si le feu n'est pas déjà prioritaire, il retient
  son ancien état, passe à `"PRIORITAIRE"` et remet son compteur à 0.
- `desactiver_prioritaire()` : si le feu est prioritaire, il repasse au rouge.
- `to_dict()` : renvoie `{"nom", "etat", "compteur"}` pour l'envoyer au client.
- `tick()` : fait tourner le feu tout seul (rouge → vert → orange → rouge).
  **Cette méthode n'est pas utilisée** : c'est le `Carrefour` qui décide de
  l'état des quatre feux en même temps (voir `regler_phase`). Un feu qui
  tournerait seul ne saurait pas ce que font les trois autres, et les feux
  pourraient se désynchroniser.

---

## 7. src/core/vehicle.py

### `__init__` : création d'une voiture

```python
def __init__(self, voie, urgence=False):
    self.voie = voie                 # voie actuelle (change quand elle tourne)
    self.origine = voie              # voie de départ (ne change jamais)
    self.urgence = urgence           # True pour un véhicule d'urgence
    self.position = self.DEPART      # elle apparaît à -180
    self.arrete = False              # True si elle n'a pas bougé au dernier tick
    self.ancienne_voie = voie        # pour dessiner le virage
    self.ancienne_position = 0       # pour dessiner le virage
    self.ticks_virage = 0            # ticks restants de l'animation de virage
    self.ticks_bloque = 0            # depuis combien de ticks elle freine pour une autre
    self.voie_libre = True           # (virage à droite) a-t-elle la place de tourner ?
    self.derriere_quelquun = False   # True si c'est la voiture de devant qui la retient
    self.ecarte = False              # True si elle se range pour une urgence
    self.decalage = 0                # décalage sur le côté, en pixels
    self.braquage = 0                # 1, -1 ou 0 : sens du décalage en cours
    self.identifiant = "voiture-" + str(id(self))
```

`voie` et `origine` sont deux choses différentes : une voiture qui vient du
nord et tourne à droite passe sur la voie `"Est"`, mais son origine reste
`"Nord"`. On a besoin des deux (par exemple pour savoir si une voiture a déjà
tourné).

```python
    if urgence:
        self.vitesse = random.randint(4, 6)      # plus rapide
        self.couleur = "red"
        self.direction = "tout_droit"            # une urgence va toujours tout droit
        self.identifiant = "urgence-" + str(id(self))
    else:
        self.vitesse = random.randint(2, 4)
        self.couleur = random.choice(self.COULEURS)
        self.direction = random.choice(self.DIRECTIONS)
```

`DIRECTIONS = ["tout_droit", "tout_droit", "gauche", "droite"]` : `tout_droit`
est écrit deux fois exprès. Comme `random.choice` tire au hasard dans la liste,
une voiture a 2 chances sur 4 d'aller tout droit, 1 sur 4 de tourner à gauche
et 1 sur 4 de tourner à droite.

### `avancer` : un pas en avant

C'est la fonction appelée à chaque tick pour chaque voiture. L'idée : on
calcule où la voiture **voudrait** aller, puis chaque règle peut **réduire**
cette position. À la fin, elle avance seulement si le résultat est plus loin
que sa position actuelle.

```python
def avancer(self, feu, devant=None):
    if self.ticks_virage > 0:
        self.ticks_virage -= 1
```
L'animation de virage avance d'un cran.

```python
    nouvelle_pos = self.position + self.vitesse
```
Là où elle irait si rien ne la gênait.

```python
    if feu.etat == "ROUGE" or feu.etat == "ORANGE":
        if self.position <= self.LIGNE_ARRET:
            nouvelle_pos = min(nouvelle_pos, self.LIGNE_ARRET)
```
Règle du feu. Si le feu est rouge ou orange **et** que la voiture n'a pas
encore passé la ligne, elle ne peut pas dépasser la ligne. Si elle l'a déjà
passée, elle continue pour dégager le carrefour. `min` garde la plus petite
des deux valeurs, donc la voiture s'arrête pile sur la ligne.

```python
    self.derriere_quelquun = False
    if devant is not None:
        limite = devant.position - self.LONGUEUR - self.ECART_MIN
```
Règle de la voiture de devant. L'avant de la voiture ne doit pas dépasser
`position de devant - 30 (sa longueur) - 10 (l'écart)`.

```python
        if devant.direction == "gauche" and self.position <= self.POINT_ATTENTE:
            limite = min(limite, self.POINT_ATTENTE)
```
Si la voiture de devant a son clignotant gauche, on ne la colle pas : on
s'arrête au point d'attente (-35). Sinon on resterait arrêté en plein milieu
du carrefour et on bloquerait les voitures d'en face qui tournent.

```python
        if nouvelle_pos > limite:
            nouvelle_pos = limite
            self.derriere_quelquun = True
```
Si la limite nous retient, on note que c'est la voiture de devant qui nous
bloque (cette information sert dans `peut_tourner`).

```python
    if self.direction == "droite":
        nouvelle_pos = min(nouvelle_pos, self.POINT_DROITE)
        if not self.voie_libre and self.position <= self.POINT_ATTENTE:
            nouvelle_pos = min(nouvelle_pos, self.POINT_ATTENTE)
    if self.direction == "gauche":
        nouvelle_pos = min(nouvelle_pos, self.POINT_GAUCHE)
```
Une voiture qui tourne s'arrête à son point de virage (-25 à droite, +25 à
gauche) : c'est le carrefour qui la fera tourner. À droite, si elle n'a pas la
place de tourner, elle attend plus en arrière (-35) pour ne gêner personne.

```python
    if nouvelle_pos > self.position:
        self.position = nouvelle_pos
        self.arrete = False
    else:
        self.arrete = True
```
Elle avance, ou bien elle est notée comme arrêtée. Une voiture ne recule
jamais.

### Les virages

```python
def au_point_de_virage(self):
```
Renvoie `True` si la voiture veut tourner et qu'elle est exactement à son point
de virage.

```python
def tourner(self):
    self.ancienne_voie = self.voie
    self.ancienne_position = self.position
    self.ticks_virage = self.DUREE_VIRAGE
```
On mémorise l'ancienne place et on lance l'animation (14 ticks, environ 0,4 s).

```python
    if self.direction == "droite":
        self.voie = self.VOIE_A_DROITE[self.voie]
        self.position = self.POINT_GAUCHE
    else:
        self.voie = self.VOIE_A_GAUCHE[self.voie]
        self.position = self.POINT_DROITE
    self.direction = "tout_droit"
    self.arrete = False
```

**Comment un virage fonctionne.** Tourner, c'est simplement **changer de voie**.
Exemple : une voiture vient du nord et tourne à droite. Elle part vers l'ouest,
donc elle roule maintenant dans le même sens que les voitures de la voie
`"Est"` (celles qui viennent de l'est et vont vers l'ouest). On change donc
`voie` en `"Est"`.

Les dictionnaires donnent la nouvelle voie :

```python
VOIE_A_DROITE = {"Nord": "Est", "Sud": "Ouest", "Ouest": "Nord", "Est": "Sud"}
VOIE_A_GAUCHE = {"Nord": "Ouest", "Sud": "Est", "Ouest": "Sud", "Est": "Nord"}
VOIE_EN_FACE  = {"Nord": "Sud", "Sud": "Nord", "Ouest": "Est", "Est": "Ouest"}
```

Et la position ? Les voies sont à 25 pixels du centre. Au moment où la voiture
venant du nord arrive à -25 (elle est à la hauteur de la voie du haut), son
avant se trouve à 25 pixels à gauche du centre. Sur la voie `"Est"`, ce point
correspond à la position +25. C'est pour ça qu'un virage à droite se fait à
`POINT_DROITE` (-25) et que la voiture arrive à `POINT_GAUCHE` (+25), et
l'inverse pour un virage à gauche. Grâce à la symétrie du carrefour, les mêmes
nombres marchent pour les quatre voies.

Ensuite `direction` redevient `"tout_droit"` pour qu'elle ne tourne pas une
deuxième fois.

### Se ranger sur le côté

```python
def changer_decalage(self, cible):
    if self.decalage < cible:
        self.decalage = min(self.decalage + 2, cible)
        self.braquage = 1
    elif self.decalage > cible:
        self.decalage = max(self.decalage - 2, cible)
        self.braquage = -1
    else:
        self.braquage = 0
```
Le décalage se rapproche de la valeur voulue de 2 pixels par tick, pour que le
mouvement soit progressif. `braquage` indique dans quel sens la voiture est en
train de se déplacer ; le client s'en sert pour la dessiner un peu de travers.

```python
def est_rangee(self):
    return self.decalage >= self.DECALAGE_VOITURE - 4
```
Vrai quand la voiture est presque complètement sur le côté (au moins 9 pixels
sur 13). Le véhicule d'urgence attend ça avant de la doubler.

### Les petites fonctions

- `est_sortie()` : vrai quand l'arrière de la voiture a dépassé 300. Elle est
  alors supprimée.
- `dans_carrefour()` : vrai si la voiture a passé la ligne d'arrêt (-70) et que
  son arrière n'est pas encore sorti du carrefour (+50).
- `rectangle()` : renvoie `[x, y, largeur, hauteur]`, le rectangle occupé par la
  voiture par rapport au centre. C'est la seule fonction du serveur qui
  convertit `voie + position` en coordonnées.
- `touche(autre)` : vrai si les rectangles des deux voitures se chevauchent. La
  méthode : deux rectangles **ne** se touchent **pas** si l'un est entièrement à
  gauche, à droite, au-dessus ou en dessous de l'autre. Si aucun de ces quatre
  cas n'est vrai, ils se touchent.
- `to_dict()` : les informations envoyées au client pour dessiner. `virage` vaut
  1 au début d'un virage et descend jusqu'à 0.

---

## 8. src/core/trafic.py

Cette classe décide **quand** une voiture arrive et **sur quelle voie**.

```python
NIVEAUX = [
    0.2, 0.2, 0.2, 0.2, 0.3, 0.5,     # 0h à 5h : la nuit
    1.0, 1.8, 2.2, 1.4, 1.0, 1.0,     # 6h à 11h : pointe du matin à 8h
    1.3, 1.2, 1.0, 1.0, 1.4, 2.2,     # 12h à 17h : pointe du soir à 17h
    2.0, 1.4, 1.0, 0.6, 0.4, 0.3,     # 18h à 23h
]
```
Une valeur par heure. `1.0` est le trafic normal, `2.2` veut dire 2,2 fois plus
de voitures. Ces valeurs sont inventées pour ressembler à une vraie journée.

```python
def __init__(self, duree_tick_s=0.03, intervalle_s=1.2, minutes_par_seconde=2):
    self.heure_de_pointe = False     # mode activé ou non
    self.minutes = 6 * 60            # heure simulée, en minutes depuis minuit
    self.reste = 0                   # voir avancer()
```

- `activer_heure_de_pointe(actif)` : active ou désactive le mode, et remet
  l'horloge à 6h00 pour qu'on voie la pointe du matin arriver.
- `heure()` : l'heure simulée, de 0 à 23.
- `heure_texte()` : l'heure sous forme de texte, par exemple `"8h05"`.
- `niveau()` : `1` en mode normal, sinon la valeur de `NIVEAUX` pour l'heure.

### `avancer` : appelée à chaque tick des véhicules

```python
def avancer(self):
    if self.heure_de_pointe:
        self.minutes += self.duree_tick_s * self.minutes_par_seconde
        if self.minutes >= 24 * 60:
            self.minutes -= 24 * 60
```
L'horloge simulée avance. Un tick dure 0,03 s et une seconde vaut 2 minutes
simulées, donc on ajoute 0,06 minute. Après 24h on revient à minuit.

```python
    self.reste += self.duree_tick_s * self.niveau() / self.intervalle_s
    arrivees = []
    while self.reste >= 1:
        self.reste -= 1
        arrivees.append(self.choisir_voie())
    return arrivees
```
C'est un **compteur qui se remplit**. En trafic normal, on ajoute
`0,03 / 1,2 = 0,025` à chaque tick. Au bout de 40 ticks (1,2 s) le compteur
atteint 1 : une voiture arrive et on retire 1. Si le niveau vaut 2,2, le
compteur se remplit 2,2 fois plus vite. La fonction renvoie la liste des voies
où une voiture arrive (souvent une liste vide).

**Pourquoi un compteur plutôt qu'un minuteur ?** Avec un minuteur il faudrait
recalculer le délai à chaque changement d'heure. Le compteur s'adapte tout seul.

### `choisir_voie`

```python
def choisir_voie(self):
    if not self.heure_de_pointe:
        return random.choice(self.VOIES)
```
En mode normal, les quatre voies ont la même chance.

```python
    heure = self.heure()
    part_nord_sud = 0.5
    if heure >= 6 and heure < 10:
        part_nord_sud = 0.75
    if heure >= 16 and heure < 20:
        part_nord_sud = 0.25

    if random.random() < part_nord_sud:
        return random.choice(["Nord", "Sud"])
    return random.choice(["Est", "Ouest"])
```
En heure de pointe, le trafic est déséquilibré : le matin 75 % des voitures
arrivent par l'avenue (nord-sud), le soir 75 % par la route (est-ouest).
`random.random()` donne un nombre entre 0 et 1 ; il est plus petit que 0,75
dans 75 % des cas.

**Pourquoi ce déséquilibre ?** C'est ce qui rend les feux adaptatifs utiles :
avec un trafic égal partout, des feux fixes 50/50 marchent déjà bien.

---

## 9. src/core/carrefour.py

C'est le fichier central : il contient les quatre feux, toutes les voitures et
toutes les règles.

### `__init__`

```python
def __init__(self, feux_settings=None, duree_tick_s=0.03, intervalle_s=1.2):
    ...
    self.feux = [self.feu_nord, self.feu_sud, self.feu_est, self.feu_ouest]
    self.feu_nord.etat = "VERT"
    self.feu_sud.etat = "VERT"
    self.feu_est.etat = "ROUGE"
    self.feu_ouest.etat = "ROUGE"
```
Quatre feux. Au départ, l'axe nord-sud est au vert.

```python
    self.vehicules = []            # les voitures visibles
    self.phase = "NS"              # quel axe a la main : "NS" ou "EW"
    self.phase_compteur = 0        # depuis combien de ticks cette phase dure
    self.urgence_voie = None       # voie de l'urgence en cours, ou None
    self.strategie = feux_settings.get("strategie", "fixe")
    self.prolongation = 0          # de combien de ticks le vert a été prolongé
    self.en_attente = {"Nord": [], "Sud": [], "Est": [], "Ouest": []}
    self.trafic = Trafic(duree_tick_s, intervalle_s)
```
`en_attente` contient, pour chaque voie, les voitures qui sont arrivées mais
qui n'ont pas encore la place d'entrer à l'écran (voir `faire_entrer`).

### Les feux en fonctionnement normal

Le principe : **un seul compteur pour les quatre feux**. La phase (`"NS"` ou
`"EW"`) dit quel axe a la main, et le compteur dit où on en est :

```
phase_compteur :  0 ───────────── 60 ─────── 66 ─────────────►
axe qui a la main:      VERT          ORANGE     ROUGE (on attend
autre axe :             ROUGE         ROUGE      que le carrefour se vide)
```

```python
def tick(self):
    if self.urgence_voie is not None:
        return
```
Pendant une urgence, le cycle normal est gelé.

```python
    if self.strategie == "adaptatif":
        self.adapter_duree_vert()
```
En mode adaptatif, on modifie éventuellement le compteur avant de l'avancer.

```python
    self.phase_compteur += 1
    duree = self.feu_nord.duree_vert + self.feu_nord.duree_orange
    if self.phase_compteur >= duree and self.carrefour_libre(None):
        if self.phase == "NS":
            self.phase = "EW"
        else:
            self.phase = "NS"
        self.phase_compteur = 0
        self.prolongation = 0
```
Quand le vert et l'orange sont finis **et que le carrefour est vide**, on passe
la main à l'autre axe. Tant qu'une voiture est encore au milieu, tout le monde
reste au rouge. C'est ce qui empêche une voiture qui démarre de percuter une
voiture qui n'a pas fini de traverser.

```python
    self.regler_phase()
```
On applique le résultat aux quatre feux.

```python
def regler_phase(self):
    ...
    for feu in self.feux:
        if feu.nom not in voies_vertes:
            feu.etat = "ROUGE"                    # l'autre axe : rouge
        elif compteur < duree_vert:
            feu.etat = "VERT"                     # début de la phase : vert
        elif compteur < duree_vert + duree_orange:
            feu.etat = "ORANGE"                   # ensuite : orange
        else:
            feu.etat = "ROUGE"                    # puis rouge en attendant
```
Cette fonction recalcule l'état des quatre feux à partir de la phase et du
compteur. Comme les quatre feux sont toujours recalculés ensemble, ils ne
peuvent pas se désynchroniser.

```python
def carrefour_libre(self, voie_autorisee):
    for v in self.vehicules:
        if v.dans_carrefour() and v.origine != voie_autorisee:
            return False
    return True
```
Vrai s'il n'y a aucune voiture dans le carrefour. Si on donne une voie, les
voitures qui viennent de cette voie ne comptent pas (utile pour l'urgence :
les voitures de la voie prioritaire ont le droit d'être là).

### Les feux adaptatifs

```python
def adapter_duree_vert(self):
    duree_vert = self.feu_nord.duree_vert
    if self.phase_compteur >= duree_vert - 1:
        return
```
On ne touche à rien une fois que le vert est fini.

```python
    if self.phase == "NS":
        demande_vert = self.demande("Nord") + self.demande("Sud")
        file_rouge = self.longueur_file("Est") + self.longueur_file("Ouest")
    else:
        ...
```
On compte deux choses : combien de voitures veulent encore passer du côté vert,
et combien attendent du côté rouge.

```python
    duree_min = duree_vert // 4
    if demande_vert == 0 and file_rouge > 0 and self.phase_compteur >= duree_min:
        self.phase_compteur = duree_vert - 1
```
**Raccourcir le vert.** S'il n'y a plus personne au vert, que des voitures
attendent au rouge, et que le vert a duré au moins un quart de sa durée
normale : on saute directement à la fin du vert. Le `+= 1` qui suit dans
`tick()` fait passer à l'orange. Le minimum d'un quart évite que les feux
changent trop vite.

```python
    elif self.phase_compteur == duree_vert - 2:
        if demande_vert > file_rouge and self.prolongation < duree_vert:
            self.phase_compteur -= 1
            self.prolongation += 1
```
**Prolonger le vert.** Juste avant la fin du vert, s'il y a plus de voitures du
côté vert que du côté rouge, on recule le compteur d'un cran : comme `tick()`
l'avance d'un cran juste après, le compteur reste sur place et le vert continue.
`prolongation` compte ces ticks en plus et les limite à `duree_vert` : le vert
peut donc durer au maximum le double de sa durée normale, pour que l'autre axe
ne soit jamais bloqué indéfiniment.

```python
def demande(self, voie):
```
Compte les voitures de cette voie qui n'ont pas encore passé la ligne d'arrêt
(arrêtées **ou** en train d'arriver), plus celles qui attendent hors écran.

```python
def longueur_file(self, voie):
```
Pareil, mais en comptant seulement les voitures **arrêtées**.

### L'urgence

```python
def declencher_urgence(self, voie_urgente):
    self.urgence_voie = voie_urgente

    for feu in self.feux:
        if feu.nom != voie_urgente or feu.etat != "PRIORITAIRE":
            feu.etat = "ROUGE"
            feu.compteur = 0
```
**Tous** les feux passent au rouge tout de suite, y compris celui de la voie
urgente (sauf s'il était déjà prioritaire). On ne lui donne pas le vert
immédiatement, car des voitures peuvent encore être au milieu du carrefour.

```python
    anciens = self.vehicules
    self.vehicules = []
    for v in anciens:
        if not v.urgence:
            self.vehicules.append(v)
```
S'il y avait déjà un véhicule d'urgence, il est retiré : il n'y en a qu'un à la
fois.

```python
    urgence = Vehicule(voie_urgente, urgence=True)
    for v in self.vehicules:
        if v.voie == voie_urgente:
            derriere = v.position - Vehicule.LONGUEUR - Vehicule.ECART_MIN
            if derriere < urgence.position:
                urgence.position = derriere
    self.vehicules.append(urgence)
    self.gerer_urgence()
```
Le véhicule d'urgence est créé **derrière la dernière voiture** de sa voie. Sans
ça, il pourrait apparaître par-dessus une voiture si la file est longue.

```python
def gerer_urgence(self):
    urgence_presente = False
    for v in self.vehicules:
        if v.urgence:
            urgence_presente = True

    if not urgence_presente:
        self.fin_urgence()
        return
```
Appelée à chaque tick des véhicules pendant une urgence. Si le véhicule
d'urgence n'est plus là (il est sorti de l'écran), l'urgence se termine toute
seule.

```python
    feu = self.trouver_feu(self.urgence_voie)
    if feu.etat != "PRIORITAIRE" and self.carrefour_libre(self.urgence_voie):
        feu.activer_prioritaire()
```
Dès que le carrefour est vide (sauf les voitures de la voie urgente), le feu de
cette voie passe en `"PRIORITAIRE"`. En pratique ça prend moins d'une seconde.

```python
def fin_urgence(self):
    if self.urgence_voie is None:
        return
    if self.urgence_voie == "Nord" or self.urgence_voie == "Sud":
        self.phase = "NS"
    else:
        self.phase = "EW"
    self.phase_compteur = self.feu_nord.duree_vert
    self.urgence_voie = None
    for feu in self.feux:
        feu.desactiver_prioritaire()
    self.regler_phase()
```
Le cycle normal reprend **à l'orange, sur l'axe de l'urgence**. Mettre le
compteur à `duree_vert` correspond exactement au début de l'orange. Ensuite le
cycle normal continue : orange, rouge le temps que le carrefour se vide, puis
vert pour l'autre axe. On ne remet pas tout à zéro brutalement, c'est ce qui
évite que les feux soient désynchronisés après une urgence.

### L'arrivée des voitures

```python
def ajouter_vehicule(self, voie):
    self.en_attente[voie].append(Vehicule(voie))
    return True
```
Une nouvelle voiture va d'abord dans la file d'attente hors écran.

```python
def generer_trafic(self):
    for voie in self.trafic.avancer():
        self.ajouter_vehicule(voie)
```
Demande à `Trafic` quelles voitures arrivent à ce tick et les ajoute.

```python
def faire_entrer(self):
    for voie in self.VOIES:
        if len(self.en_attente[voie]) == 0:
            continue
        place_libre = True
        for v in self.vehicules:
            if v.voie == voie and v.position < Vehicule.DEPART + 50:
                place_libre = False
        if place_libre:
            self.vehicules.append(self.en_attente[voie].pop(0))
```
Pour chaque voie, si une voiture attend et que l'entrée de la voie est libre
(aucune voiture dans les 50 premiers pixels), la plus ancienne entre.
`pop(0)` retire et renvoie le premier élément : premier arrivé, premier entré.

**Pourquoi cette file ?** Avant, quand la voie était pleine, la nouvelle
voiture était simplement perdue. Avec la file, aucune voiture ne disparaît, et
la longueur des files est réaliste même quand la queue dépasse l'écran.

### `peut_tourner` : a-t-on le droit de tourner ?

```python
def peut_tourner(self, vehicule):
    if vehicule.direction == "droite":
        nouvelle_voie = Vehicule.VOIE_A_DROITE[vehicule.voie]
        nouvelle_pos = Vehicule.POINT_GAUCHE
    else:
        nouvelle_voie = Vehicule.VOIE_A_GAUCHE[vehicule.voie]
        nouvelle_pos = Vehicule.POINT_DROITE
    en_face = Vehicule.VOIE_EN_FACE[vehicule.voie]
    feu_en_face = self.trouver_feu(en_face)
    place = Vehicule.LONGUEUR + Vehicule.ECART_MIN
```
On calcule où la voiture arriverait (voie et position), quelle est la voie d'en
face, et la place qu'il faut (40 pixels).

Ensuite on regarde toutes les autres voitures. Dès qu'une règle dit non, on
renvoie `False`.

```python
        if autre.voie == nouvelle_voie:
            if abs(autre.position - nouvelle_pos) < place:
                return False
```
**Règle 1 : il faut de la place à l'arrivée.** Une voiture est déjà à moins de
40 pixels de l'endroit où on arriverait.

```python
            if vehicule.direction == "droite":
                if autre.position > Vehicule.LIGNE_ARRET and autre.position < nouvelle_pos:
                    return False
```
**Règle 2 : à droite, on ne coupe pas la route.** Une voiture est déjà engagée
dans le carrefour sur la voie qu'on veut rejoindre, et elle va passer devant
nous.

```python
        if vehicule.direction == "gauche" and autre.voie == en_face:
            if autre.position > Vehicule.POINT_ATTENTE and autre.position < 15:
                return False
```
**Règle 3 : à gauche, le passage doit être dégagé.** Une voiture d'en face se
trouve exactement là où on doit passer (entre -35 et 15), même arrêtée.

```python
            if autre.direction == "droite" and autre.voie_libre:
                if autre.position > Vehicule.LIGNE_ARRET and not autre.derriere_quelquun:
                    return False
```
**Règle 4.** Une voiture d'en face est en train de tourner à droite : elle a la
place et personne ne la retient. Elle va venir sur la voie où on veut aller,
donc on la laisse passer.

```python
            if not autre.arrete and autre.position < 20:
                if autre.position > Vehicule.LIGNE_ARRET:
                    return False
                if feu_en_face.etat == "VERT" or feu_en_face.etat == "PRIORITAIRE":
                    return False
```
**Règle 5 : priorité aux voitures d'en face qui roulent.** C'est la règle du
code de la route. Une voiture d'en face qui roule nous bloque si elle a déjà
passé sa ligne, ou si son feu est vert. Si son feu est rouge et qu'elle n'a pas
passé la ligne, elle va s'arrêter : on peut y aller. Les voitures arrêtées sont
ignorées ici, sinon deux voitures qui tournent à gauche face à face
attendraient chacune la file de l'autre pour toujours.

### `ecarter_vehicules` : laisser passer l'urgence

```python
def ecarter_vehicules(self):
    urgence = self.trouver_urgence()
    voiture_ecartee = False

    for v in self.vehicules:
        if v.urgence:
            continue
        v.ecarte = False
```
On cherche le véhicule d'urgence. Par défaut, aucune voiture n'est rangée.

```python
        if urgence is not None and v.voie == urgence.voie:
            distance = v.position - urgence.position
            pas_encore_doublee = distance > -Vehicule.LONGUEUR
            if pas_encore_doublee and distance < Vehicule.DISTANCE_SIRENE:
                if not v.dans_carrefour() and v.ticks_virage == 0:
                    v.ecarte = True
                    voiture_ecartee = True
```
Une voiture se range si **toutes** ces conditions sont vraies :
- elle est sur la même voie que l'urgence ;
- l'urgence ne l'a pas encore complètement doublée (`distance > -30`) ;
- l'urgence est à moins de 160 pixels derrière elle ;
- elle n'est pas dans le carrefour (on ne s'arrête pas au milieu) ;
- elle n'est pas en plein virage.

```python
        if v.ecarte:
            v.changer_decalage(Vehicule.DECALAGE_VOITURE)
        else:
            v.changer_decalage(0)
```
Une voiture rangée glisse vers le bord (13 pixels), les autres reviennent à
leur place (0). Comme c'est recalculé à chaque tick, une voiture reprend sa
place toute seule dès qu'elle a été doublée.

```python
    if urgence is not None:
        if voiture_ecartee:
            urgence.changer_decalage(Vehicule.DECALAGE_URGENCE)
        else:
            urgence.changer_decalage(0)
```
Le véhicule d'urgence se décale de 11 pixels vers le milieu de la route tant
qu'il a des voitures à doubler.

**Vérification des largeurs.** Une voie va de 15 à 35 pixels du centre. Une
voiture rangée occupe 28 à 48 (la route s'arrête à 50). L'urgence décalée
occupe 4 à 24. Il reste 4 pixels entre les deux : elles ne se touchent pas.

### `est_bloque`

```python
def est_bloque(self, vehicule):
    for autre in self.vehicules:
        if autre.voie != vehicule.voie and vehicule.touche(autre):
            return True
    return False
```
Vrai si la voiture touche une voiture d'une **autre** voie. Les voitures de la
même voie sont déjà gérées par la règle « voiture de devant ».

### `avancer_vehicules` : un tick complet

C'est la fonction appelée toutes les 30 ms. Elle fait tout dans l'ordre.

```python
def avancer_vehicules(self):
    self.faire_entrer()
    self.ecarter_vehicules()
```
Étape 1 : faire entrer les voitures qui attendent. Étape 2 : décider qui se
range pour l'urgence.

```python
    for feu in self.feux:
        voitures = []
        for v in self.vehicules:
            if v.voie == feu.nom:
                voitures.append(v)
        voitures.sort(key=position_vehicule, reverse=True)
```
Étape 3 : on traite les voies une par une. Pour chaque feu, on prend les
voitures de sa voie et on les trie de la plus avancée à la moins avancée.
`position_vehicule` est une petite fonction en haut du fichier qui renvoie la
position d'une voiture ; `sort` s'en sert pour trier. Le tri est indispensable :
chaque voiture doit connaître celle qui est juste devant elle, et la voiture de
devant doit avoir bougé en premier.

```python
        devant = None
        devant_urgence = None
        for v in voitures:
            if v.ecarte and v.position <= Vehicule.LIGNE_ARRET:
                v.arrete = True
```
Une voiture rangée avant le carrefour ne bouge pas. Une voiture rangée après le
carrefour continue de rouler sur le bord (elle passe dans le `else`).

```python
            else:
                ancienne_pos = v.position
                deja_bloque = self.est_bloque(v)
                if v.direction == "droite":
                    v.voie_libre = self.peut_tourner(v)
                if v.urgence:
                    v.avancer(feu, devant_urgence)
                else:
                    v.avancer(feu, devant)
```
On retient l'ancienne position, puis on fait avancer la voiture. Avant, pour
une voiture qui va tourner à droite, on calcule si elle a la place. Le véhicule
d'urgence reçoit une « voiture de devant » différente : la première voiture qui
n'est **pas** rangée.

```python
                if not deja_bloque and self.est_bloque(v):
                    v.ticks_bloque += 1
                    if v.ticks_bloque < Vehicule.PATIENCE:
                        v.position = ancienne_pos
                        v.arrete = True
                else:
                    v.ticks_bloque = 0
```
**Le freinage.** Si la voiture ne touchait personne avant d'avancer et qu'elle
touche une voiture qui croise après avoir avancé, on annule son mouvement : elle
freine. `ticks_bloque` compte depuis combien de temps. Au bout de 70 ticks
(environ 2 secondes) elle passe quand même : c'est une sécurité pour que le
carrefour ne reste jamais coincé si deux voitures se bloquent mutuellement.

```python
            devant = v
            if not v.est_rangee():
                devant_urgence = v
```
La voiture qu'on vient de traiter devient la « voiture de devant » pour la
suivante. Pour le véhicule d'urgence, seules les voitures pas encore rangées
comptent : il peut doubler les autres.

```python
    for v in self.vehicules:
        if v.au_point_de_virage() and self.peut_tourner(v):
            v.tourner()
```
Étape 4 : les virages. Ils sont faits **après** tous les déplacements. Sinon une
voiture qui change de voie pourrait être déplacée une deuxième fois dans le même
tick, quand on traite sa nouvelle voie.

```python
    restants = []
    for v in self.vehicules:
        if not v.est_sortie():
            restants.append(v)
    self.vehicules = restants
```
Étape 5 : on garde seulement les voitures qui ne sont pas sorties de l'écran.

```python
    if self.urgence_voie is not None:
        self.gerer_urgence()
```
Étape 6 : pendant une urgence, on vérifie à chaque tick (toutes les 30 ms) si on
peut donner la priorité ou si l'urgence est finie. C'est fait ici et pas dans
`tick()` pour que la réaction soit rapide.

### `get_state`

Construit le dictionnaire envoyé aux clients : la liste des feux, la liste des
véhicules, le nombre de véhicules par voie (`densite`), la voie de l'urgence, la
stratégie et les informations de trafic. `compter_vehicules(voie)` compte les
voitures d'une voie.

---

## 10. src/network/protocol.py

Ce fichier définit le format des messages.

```python
def encode_message(payload):
    texte = json.dumps(payload, ensure_ascii=False) + "\n"
    return texte.encode("utf-8")
```
- `json.dumps` transforme un dictionnaire en texte JSON.
- `ensure_ascii=False` garde les accents tels quels.
- `+ "\n"` ajoute le retour à la ligne qui marque la fin du message.
- `.encode("utf-8")` transforme le texte en octets, car un socket n'envoie que
  des octets.

```python
def decode_messages(buffer):
    messages = []
    while b"\n" in buffer:
        morceaux = buffer.split(b"\n", 1)
        raw_message = morceaux[0]
        buffer = morceaux[1]
        if raw_message.strip() == b"":
            continue
        message = json.loads(raw_message.decode("utf-8"))
        messages.append(message)
    return messages, buffer
```
`buffer` contient les octets reçus et pas encore traités. Tant qu'il contient
un retour à la ligne, on coupe en deux au premier retour à la ligne : la partie
avant est un message complet, la partie après reste dans le buffer. La fonction
renvoie les messages complets **et le reste**.

**Pourquoi c'est nécessaire.** Avec TCP, `recv` peut renvoyer un demi-message,
ou deux messages et demi d'un coup. Le reste du buffer est gardé et complété au
prochain `recv`.

Les messages :

| Sens | Message |
|---|---|
| serveur → client | `{"type": "state", "payload": {...}}` : l'état complet |
| serveur → client | `{"type": "error", "message": "..."}` |
| client → serveur | `{"type": "command", "action": "trigger_emergency", "road": "Nord"}` |
| client → serveur | `{"type": "command", "action": "clear_emergency"}` |
| client → serveur | `{"type": "command", "action": "set_rush_hour", "value": true}` |
| client → serveur | `{"type": "command", "action": "set_strategy", "value": "adaptatif"}` |

**Pourquoi envoyer l'état complet à chaque fois ?** C'est le plus simple et le
plus robuste : un client qui se connecte en cours de route a tout de suite tout
ce qu'il faut, et un message perdu ou en retard n'a aucune conséquence.

---

## 11. src/network/server.py

### `__init__`

```python
self.tick_s = tick_ms / 1000
self.vehicle_tick_s = vehicle_tick_ms / 1000
self.spawn_tick_s = spawn_tick_ms / 1000
```
Conversion des millisecondes en secondes.

```python
tick_duration = max(self.tick_s, 0.001)
feux_en_ticks = {}
for nom in ["duree_vert_s", "duree_orange_s", "duree_rouge_s"]:
    nb_ticks = round(feux_settings.get(nom, 0) / tick_duration)
    if nb_ticks < 1:
        nb_ticks = 1
    feux_en_ticks[nom] = nb_ticks
```
Conversion des durées des feux de secondes en ticks (30 s / 0,5 s = 60 ticks).
`max(..., 0.001)` évite une division par zéro, et chaque durée vaut au moins 1
tick.

```python
self.carrefour = Carrefour(feux_en_ticks, self.vehicle_tick_s, self.spawn_tick_s)
self.logger = EventLogger(log_path)
self.clients = []                          # les sockets des clients connectés
self.carrefour_lock = threading.Lock()     # protège le carrefour
self.clients_lock = threading.Lock()       # protège la liste des clients
self.threads = []
```

### `start`

```python
self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
Crée un socket. `AF_INET` = adresses IPv4, `SOCK_STREAM` = TCP.

```python
self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```
Permet de relancer le serveur tout de suite après l'avoir arrêté, sans attendre
que le système libère le port.

```python
self.server_socket.bind((self.host, self.port))
self.server_socket.listen()
self.server_socket.settimeout(1.0)
```
`bind` réserve l'adresse et le port, `listen` commence à écouter. Le timeout
d'une seconde fait que `accept` ne bloque pas pour toujours : la boucle peut
vérifier régulièrement si le serveur doit s'arrêter.

```python
accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
```
Deux threads : un qui accepte les clients, un qui fait tourner la simulation.
`daemon=True` : ces threads s'arrêtent automatiquement quand le programme
principal se termine.

### `accept_loop` et `handle_client`

`accept_loop` attend les connexions. Pour chaque client : il l'ajoute à la
liste (sous verrou) et lance un nouveau thread `handle_client` pour lui.

`handle_client` tourne en boucle pour un client : il reçoit des octets avec
`recv(4096)`, les ajoute au buffer, découpe les messages complets avec
`decode_messages` et appelle `handle_message` pour chacun. Si `recv` renvoie
des octets vides, le client s'est déconnecté : on sort de la boucle et on le
retire de la liste.

### `handle_message`

```python
if message.get("type") != "command":
    self.send_error(client_socket, "Message invalide")
    return
action = message.get("action")
self.carrefour_lock.acquire()
if action == "trigger_emergency":
    voie = message.get("road")
    if voie in Carrefour.VOIES:
        self.carrefour.declencher_urgence(voie)
        self.logger.log("urgence", voie)
    else:
        self.send_error(client_socket, "Voie inconnue")
elif action == "clear_emergency": ...
elif action == "set_rush_hour": ...
elif action == "set_strategy": ...
else:
    self.send_error(client_socket, "Commande inconnue")
self.carrefour_lock.release()
```
Le serveur **vérifie tout ce qu'il reçoit** : le type du message, que la voie
existe, que la stratégie est bien `"fixe"` ou `"adaptatif"`. On ne fait jamais
confiance à ce qui vient du réseau. Le verrou est pris avant de toucher au
carrefour et relâché après. Chaque commande est enregistrée dans le journal.

### `simulation_loop`

```python
last_tick = time.monotonic()
last_vehicle_tick = time.monotonic()
last_broadcast = time.monotonic()
```
On note l'heure de départ. `time.monotonic()` est une horloge qui ne recule
jamais (contrairement à l'heure du système, qui peut être modifiée).

```python
while self.running:
    now = time.monotonic()
    self.carrefour_lock.acquire()
    if now - last_tick >= self.tick_s:
        self.carrefour.tick()
        last_tick = now
```
Si 0,5 s s'est écoulée depuis le dernier tick des feux, on en fait un.

```python
    if now - last_vehicle_tick >= self.vehicle_tick_s:
        self.carrefour.generer_trafic()
        self.carrefour.avancer_vehicules()
        last_vehicle_tick = now
```
Si 30 ms se sont écoulées : de nouvelles voitures arrivent éventuellement, puis
toutes les voitures bougent.

```python
    state = None
    if now - last_broadcast >= self.vehicle_tick_s:
        state = self.carrefour.get_state()
        last_broadcast = now
    self.carrefour_lock.release()

    if state is not None:
        self.broadcast_state(state)
    time.sleep(0.01)
```
On copie l'état **sous verrou**, puis on relâche le verrou **avant** de
l'envoyer. L'envoi réseau peut être lent ; il ne doit pas bloquer la
simulation. `sleep(0.01)` évite que la boucle utilise 100 % du processeur.

### `broadcast_state`

Encode l'état une seule fois, puis l'envoie à chaque client avec `sendall`. Si
l'envoi échoue (client parti), le client est retiré de la liste. On parcourt
une **copie** de la liste, parce qu'on ne peut pas modifier une liste pendant
qu'on la parcourt.

---

## 12. src/network/client.py

```python
def start(self):
    self.running = True
    self.thread = threading.Thread(target=self.run, daemon=True)
    self.thread.start()
```
Le client réseau tourne dans son propre thread. **Pourquoi ?** `recv` bloque en
attendant des données. Dans le thread principal, ça gèlerait la fenêtre.

```python
def run(self):
    while self.running:
        if not self.connected:
            self.connect()
            if not self.connected:
                time.sleep(self.reconnect_delay)
                continue
        try:
            self.receive_loop()
        except OSError as error:
            self.last_error = str(error)
        self.close_socket()
```
Boucle de reconnexion automatique : si on n'est pas connecté, on essaie ; si ça
échoue, on attend 2 s et on recommence. On peut donc lancer le client avant le
serveur, ou redémarrer le serveur sans relancer le client.

```python
def receive_loop(self):
    ...
    for message in messages:
        if message.get("type") == "state":
            self.lock.acquire()
            self.latest_state = message.get("payload")
            self.lock.release()
```
À chaque état reçu, on **remplace** l'ancien. On ne garde que le plus récent :
si la fenêtre est en retard, elle saute les anciens états au lieu d'accumuler
du retard.

```python
def consume_latest_state(self):
    self.lock.acquire()
    state = self.latest_state
    self.latest_state = None
    self.lock.release()
    return state
```
La fenêtre appelle cette fonction pour récupérer le dernier état. Il est remis
à `None` pour ne pas redessiner deux fois la même chose. Le verrou protège
`latest_state`, qui est écrit par le thread réseau et lu par le thread de la
fenêtre.

```python
def send_command(self, action, road=None, value=None):
    message = {"type": "command", "action": action}
    if road is not None:
        message["road"] = road
    if value is not None:
        message["value"] = value
    self.socket.sendall(encode_message(message))
```
Construit et envoie une commande. `road` et `value` ne sont ajoutés que si on
les donne.

---

## 13. src/ui (interface graphique)

### main_window.py

La fenêtre contient le dessin (`CarrefourWidget`) à gauche et les boutons
(`ControlPanel`) à droite.

```python
self.poll_timer = QTimer()
self.poll_timer.timeout.connect(self.poll_server)
self.poll_timer.start(50)
```
Un minuteur Qt appelle `poll_server` toutes les 50 ms.

```python
def poll_server(self):
    latest_state = self.network_client.consume_latest_state()
    if latest_state is not None:
        self.carrefour_widget.set_state(latest_state)
        self.control_panel.set_density(...)
        ...
```
**Pourquoi un minuteur ?** Dans Qt, seul le thread principal a le droit de
toucher à l'interface. Le thread réseau ne peut donc pas redessiner lui-même.
La solution : le thread réseau range l'état dans une variable, et le thread
principal vient le chercher régulièrement.

Les fonctions `trigger_emergency`, `clear_emergency`, `set_rush_hour` et
`set_strategy` envoient simplement la commande correspondante au serveur.

### control_panel.py

Le panneau reçoit des **fonctions** en paramètre (`on_trigger_emergency`,
etc.). Quand on clique sur un bouton, il appelle la fonction reçue. Le panneau
ne connaît donc pas le réseau : c'est `MainWindow` qui fait le lien.

Il y a une méthode par bouton d'urgence (`urgence_nord`, `urgence_sud`...) :
c'est plus long qu'une boucle, mais beaucoup plus simple à lire.

```python
def changer_heure_de_pointe(self):
    self.on_set_rush_hour(not self.heure_de_pointe)
```
Le bouton demande l'inverse de l'état actuel.

**Point important :** le bouton ne change pas son texte lui-même. Il envoie la
commande, et c'est quand le serveur renvoie le nouvel état que `set_trafic` et
`set_strategie` mettent le texte à jour. Ainsi l'affichage montre toujours
l'état réel du serveur, même s'il y a plusieurs clients ou si la commande est
refusée.

### carrefour_widget.py

`paintEvent` est appelée par Qt chaque fois que le widget doit être redessiné.
Elle dessine dans cet ordre, du fond vers le dessus :

```python
self.dessiner_decor(painter)       # bâtiments, parc
self.dessiner_routes(painter)      # trottoirs, chaussée, bandes cyclables, terre-plein
self.dessiner_marquage(painter)    # pointillés, passages piétons, lignes d'arrêt
self.dessiner_vehicules(painter)   # les voitures
self.dessiner_feux(painter)        # les feux
self.dessiner_panneaux(painter)    # textes
```
L'ordre compte : ce qui est dessiné en dernier passe par-dessus.

Tout est placé par rapport au centre du widget (`centre_x`, `centre_y`), donc
le dessin reste centré quand on change la taille de la fenêtre.

```python
def position_voiture(self, voie, position, longueur, decalage=0):
    milieu = position - longueur / 2
    cote = 25 + decalage
    if voie == "Nord":
        return [self.centre_x - cote, self.centre_y + milieu, 180]
    if voie == "Sud":
        return [self.centre_x + cote, self.centre_y - milieu, 0]
    if voie == "Ouest":
        return [self.centre_x + milieu, self.centre_y + cote, 90]
    return [self.centre_x - milieu, self.centre_y - cote, 270]
```
C'est ici que `voie + position` devient des pixels. La fonction renvoie le
centre de la voiture (x, y) et son angle. `milieu` est la position du centre de
la voiture (l'avant moins la moitié de la longueur). `cote` est la distance
entre le centre de la route et la voie : 25, plus le décalage quand la voiture
se range. L'angle 0 veut dire « vers le haut ».

```python
def dessiner_vehicules(self, painter):
    clignote = int(time.monotonic() * 3) % 2 == 0
```
Vaut `True` puis `False` en alternance, trois changements par seconde : c'est
le rythme du clignotant.

```python
        angle = place[2] + 9 * vehicle.get("braquage", 0)
```
Une voiture qui se décale est dessinée tournée de 9 degrés.

```python
        reste = vehicle.get("virage", 0)
        if reste > 0:
            ancienne = self.position_voiture(vehicle["ancienne_voie"], vehicle["ancienne_position"], longueur)
            ecart = angle - ancienne[2]
            if ecart > 180:
                ecart -= 360
            if ecart < -180:
                ecart += 360
            x = x + (ancienne[0] - x) * reste
            y = y + (ancienne[1] - y) * reste
            angle = angle - ecart * reste
```
**L'animation du virage.** Dans la simulation, la voiture change de voie d'un
seul coup. Pour que ce soit joli, le dessin fait un mélange entre l'ancienne
place et la nouvelle. `reste` vaut 1 au début du virage (on dessine l'ancienne
place) et descend jusqu'à 0 (on dessine la nouvelle). Entre les deux, la
voiture glisse et pivote progressivement. Les deux `if` sur `ecart` servent à
tourner par le chemin le plus court : pour passer de 270° à 0°, on tourne de
+90° et pas de -270°.

```python
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        ...
        painter.restore()
```
Au lieu de calculer les coins d'un rectangle tourné, on déplace et on tourne
**la feuille de dessin**, on dessine la voiture toujours de la même façon
(vers le haut, centrée en 0,0), puis on remet la feuille comme avant.

Dans ce repère : le corps de la voiture, le pare-brise bleu clair vers l'avant,
et un petit carré orange dans le coin avant gauche ou droit si la voiture va
tourner.

`dessiner_urgence` dessine le contour jaune, la bande blanche et les deux
gyrophares. `int(time.monotonic() * 6) % 2` fait échanger les couleurs bleu et
blanc six fois par seconde.

### vehicle_widget.py

`couleur_vehicule(vehicle)` : rouge pour une urgence, sinon la couleur de la
voiture.

---

## 14. src/utils

### config_loader.py

```python
DOSSIER_PROJET = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SETTINGS_PATH = os.path.join(DOSSIER_PROJET, "config", "settings.json")
```
`__file__` est le chemin de ce fichier. `dirname` remonte d'un dossier ; trois
fois de suite on passe de `src/utils/config_loader.py` à la racine du projet.
Le fichier de config est ainsi trouvé quel que soit le dossier d'où on lance le
programme.

`load_settings()` ouvre le fichier, le lit avec `json.load` et renvoie un
dictionnaire.

### logger.py

`EventLogger` enregistre les événements dans une base SQLite.

- `__init__` : crée le dossier `logs/` s'il n'existe pas, puis la table
  `events` (`id`, `date`, `type`, `details`) si elle n'existe pas.
- `log(event_type, details)` : ajoute une ligne avec la date et l'heure.
- `get_events()` : renvoie tous les événements dans une liste de dictionnaires.

```python
connection.execute(
    "INSERT INTO events (date, type, details) VALUES (?, ?, ?)",
    (date, event_type, details),
)
```
Les `?` sont remplacés par les valeurs par SQLite lui-même. On ne colle jamais
les valeurs directement dans le texte de la requête : c'est la protection
contre les injections SQL.

Une connexion est ouverte et fermée à chaque appel. C'est moins rapide, mais
une connexion SQLite ne doit pas être partagée entre plusieurs threads, et le
serveur écrit depuis plusieurs threads.

---

## 15. main.py et server.py

`main.py` (client) : lit la config, crée l'application Qt et la fenêtre, et
lance la boucle d'événements Qt avec `app.exec()`.

`server.py` (serveur) : lit la config, crée le `SimulationServer` et le
démarre. Ensuite :

```python
try:
    while True:
        time.sleep(0.2)
except KeyboardInterrupt:
    pass
server.stop()
```
Le thread principal ne fait qu'attendre, pendant que les autres threads
travaillent. Ctrl+C déclenche `KeyboardInterrupt`, on sort de la boucle et on
arrête proprement le serveur.

`if __name__ == "__main__":` : le code n'est exécuté que si on lance le fichier
directement, pas s'il est importé par un autre fichier.

---

## 16. Problèmes rencontrés et solutions

| Problème | Cause | Solution |
|---|---|---|
| Le véhicule d'urgence ne se voyait pas | Rouge simple, et des voitures normales pouvaient être rouge foncé | Contour jaune, bande blanche, gyrophare bleu clignotant ; `darkred` retiré des couleurs |
| Feux désynchronisés après une urgence | Tout passait au rouge puis repartait de zéro | Le cycle reprend à l'orange sur l'axe de l'urgence (`fin_urgence`) |
| Voitures qui se percutaient pendant une urgence | La voie urgente passait au vert alors que des voitures étaient encore au milieu | La priorité n'est donnée que lorsque le carrefour est vide (`gerer_urgence`) |
| Voitures qui se percutaient au changement de feu | Pas de temps mort entre les deux axes | L'autre axe attend que le carrefour soit vide (`tick`) |
| L'urgence apparaissait sur une voiture | Elle était créée à une position fixe | Elle est créée derrière la dernière voiture de la voie |
| Virage à gauche à travers une voiture arrêtée | La voiture suivante s'arrêtait au milieu du carrefour | Elle attend en retrait (`POINT_ATTENTE`) ; règle 3 de `peut_tourner` |
| Virage à droite qui coupait la route | Seule la distance était vérifiée | Règles 2 et 4 de `peut_tourner`, attente en retrait |
| Risque de carrefour bloqué | Deux voitures qui s'attendent l'une l'autre | Les voitures arrêtées sont ignorées (règle 5) et sécurité `PATIENCE` |
| Voitures perdues quand une voie était pleine | La nouvelle voiture était refusée | File d'attente hors écran (`en_attente`) |
| Virages saccadés | La voiture changeait de voie d'un coup | Animation côté client (`virage`) |

Les collisions ont existé un moment dans le projet (détection et affichage),
puis elles ont été retirées : le choix final est d'**empêcher** les voitures de
se toucher plutôt que de constater les accidents.

---

## 17. Limites et code non utilisé

À connaître pour répondre honnêtement si on pose la question.

**Simplifications**
- Une seule voie par sens, alors que le vrai carrefour en a plusieurs.
- Les bâtiments et le parc sont décoratifs, ils ne correspondent pas aux vrais
  alentours.
- Les voitures démarrent et s'arrêtent instantanément (pas d'accélération).
- Un seul véhicule d'urgence à la fois, et il va toujours tout droit.
- Pas de piétons ni de vélos.
- Dans de rares cas (environ une fois par demi-heure de simulation), deux
  voitures peuvent encore se chevaucher brièvement à l'écran.

**Code présent mais pas utilisé par le serveur**
- `Feu.tick()`, `Feu.duree_rouge`, `Feu.etat_precedent` : le carrefour pilote
  les feux lui-même.
- `src/core/simulateur.py` : petite classe qui fait tourner un carrefour sans
  réseau. Elle date du début du projet.
- `src/core/pathfinder.py` : algorithme de Dijkstra sur un graphe des quatre
  voies. Il n'est appelé nulle part, car dans un seul carrefour le trajet d'un
  véhicule d'urgence est toujours direct.
- `settings.json` : `simulation.nb_voies`, `feux.duree_rouge_s` et
  `carrefour.largeur_px` / `hauteur_px` ne sont pas utilisés.
- Les fichiers du dossier `tests/` sont vides.

---

## 18. Questions possibles à la soutenance

**Pourquoi TCP et pas UDP ?**
TCP garantit que tout arrive, dans l'ordre. Une commande d'urgence perdue
serait grave. UDP serait plus léger, mais il faudrait gérer les pertes à la
main.

**Comment séparez-vous les messages ?**
Chaque message est une ligne JSON terminée par `\n`. Le récepteur garde les
octets reçus dans un buffer et coupe à chaque `\n`.

**Pourquoi des verrous ?**
Le thread de simulation et les threads des clients modifient le même carrefour.
Sans verrou, une commande pourrait modifier la liste des voitures pendant que
la simulation la parcourt.

**Que se passe-t-il si le serveur tombe ?**
Le client affiche « déconnectée » et réessaie toutes les 2 secondes. Quand le
serveur revient, l'affichage repart tout seul.

**Comment les feux restent-ils synchronisés ?**
Il n'y a qu'un seul compteur pour les quatre feux (`phase` et
`phase_compteur`). Les quatre états sont recalculés ensemble dans
`regler_phase`.

**Comment marche la priorité d'urgence ?**
Tous les feux passent au rouge immédiatement. Dès que le carrefour est vide, le
feu de la voie urgente passe en prioritaire. Les voitures devant le véhicule se
rangent à droite. Quand il est sorti, le cycle reprend à l'orange.

**En quoi le carrefour est-il « intelligent » ?**
Il détecte l'urgence et adapte les feux tout seul, et en mode adaptatif il
règle la durée du vert selon le nombre de voitures sur chaque axe.

**Comment marchent les feux adaptatifs ?**
Deux règles : le vert s'arrête plus tôt si plus personne n'arrive et que
l'autre axe attend ; il est prolongé (au maximum doublé) s'il y a plus de
voitures du côté vert que du côté rouge.

**Comment une voiture sait-elle qu'elle doit s'arrêter ?**
À chaque tick, on calcule où elle voudrait aller, puis chaque règle (feu,
voiture de devant, point de virage) peut réduire cette position. Si le résultat
n'est pas plus loin que sa position actuelle, elle reste sur place.

**Comment fonctionne un virage ?**
La voiture s'arrête à son point de virage. Quand `peut_tourner` dit oui, elle
change de voie : sa `voie` et sa `position` sont remplacées. Le client anime le
passage pour que ce soit progressif.
