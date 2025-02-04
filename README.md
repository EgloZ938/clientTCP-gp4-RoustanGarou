# Client TCP Loup-Garou

Ce projet est un client TCP avec interface graphique Tkinter pour le jeu Loup-Garou. Il permet aux joueurs de se connecter à un serveur de jeu et de participer à une partie de Loup-Garou en réseau.

## Fonctionnalités

- Interface graphique intuitive avec Tkinter
- Connexion TCP au serveur de jeu
- Système de chat en temps réel
- Gestion des rôles (Loup-Garou/Villageois)
- Communication asynchrone avec le serveur

## Prérequis

- Python 3.x
- Tkinter (généralement inclus avec Python)
- Socket (bibliothèque standard Python)
- Threading (bibliothèque standard Python)
- JSON (bibliothèque standard Python)

## Installation

1. Clonez ce dépôt :
```bash
git clone [URL_DU_REPO]
cd loup-garou-client
```

2. Assurez-vous que Python 3.x est installé :
```bash
python --version
```

3. Lancez le client :
```bash
python client_tcp.py
```

## Utilisation

1. Démarrage du client :
   - Exécutez le script `client_tcp.py`
   - Une fenêtre Tkinter s'ouvrira

2. Connexion à une partie :
   - Entrez votre nom dans le champ "Nom du joueur"
   - Entrez l'ID de la partie dans le champ "ID Partie"
   - Cliquez sur "Connexion"

3. Dans le jeu :
   - Utilisez la zone de chat pour communiquer
   - Attendez l'attribution de votre rôle
   - Suivez les instructions du jeu

## Structure du Code

```
LoupGarouClient
│
├── __init__()                 # Initialisation de l'interface
├── setup_gui()               # Configuration de l'interface graphique
├── connect_to_server()       # Gestion de la connexion TCP
├── send_message()           # Envoi de messages au serveur
├── receive_messages()       # Réception des messages du serveur
├── handle_message()         # Traitement des messages reçus
├── add_message()           # Ajout de messages dans le chat
└── cleanup()               # Nettoyage des ressources
```

## Configuration

Par défaut, le client se connecte à :
- Hôte : localhost
- Port : 12345

Pour modifier ces paramètres, changez les valeurs dans la méthode `connect_to_server()`.

## Base de Données

Le système utilise une base de données avec les tables suivantes :

### PARTIE
| Champ          | Type        | Description                    |
|----------------|-------------|--------------------------------|
| id_game        | int         | Identifiant unique de la partie|
| nb_player      | int         | Nombre de joueurs             |
| size_map       | varchar(10) | Taille de la carte            |
| nb_wave_max    | int         | Nombre maximum de vagues      |
| max_time_tour  | int         | Temps maximum par tour        |

### JOUEUR
| Champ          | Type        | Description                    |
|----------------|-------------|--------------------------------|
| id_player      | int         | Identifiant unique du joueur  |
| name           | varchar(10) | Nom du joueur                 |

### JOINTURE
| Champ          | Type        | Description                    |
|----------------|-------------|--------------------------------|
| id_game        | int         | Identifiant de la partie      |
| id_player      | int         | Identifiant du joueur         |
| is_alive       | bool        | État du joueur                |
| role           | bool        | Rôle (true=villageois, false=loup)|

## Protocole de Communication

Le client utilise JSON pour communiquer avec le serveur. Formats des messages :

### Connexion
```json
{
    "type": "connection",
    "name": "nom_joueur",
    "game_id": "id_partie"
}
```

### Message de Chat
```json
{
    "type": "message",
    "content": "contenu_message",
    "game_id": "id_partie",
    "player": "nom_joueur"
}
```