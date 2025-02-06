import socket
import threading
import json
import random
from typing import Dict, List
from game_logic import GameLogic

class GameRoom:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players: Dict[socket.socket, dict] = {}  # socket -> {name: str, role: None}
        self.messages: List[dict] = []
        self.started = False
        self.game_logic = GameLogic()
        self.current_turn = None
        self.min_players = 4  # Minimum requis pour démarrer
        self.announced_deaths = set()  # Nouvelle liste pour tracker les morts annoncées

    def add_player(self, client_socket: socket.socket, player_name: str) -> None:
        """Ajoute un joueur sans rôle"""
        self.players[client_socket] = {
            "name": player_name,
            "role": None
        }
        self.broadcast_player_list()
        
        # Vérifie si on peut démarrer
        if len(self.players) >= self.min_players:
            self.broadcast_system_message(f"La partie peut démarrer ! ({len(self.players)} joueurs connectés)")

    def assign_roles(self) -> None:
        """Attribue les rôles aléatoirement"""
        player_sockets = list(self.players.keys())
        nb_players = len(player_sockets)
        nb_wolves = max(1, nb_players // 4)  # 1 loup pour 4 joueurs

        # Mélange la liste et assigne les rôles
        random.shuffle(player_sockets)
        
        for i, socket in enumerate(player_sockets):
            role = "loup" if i < nb_wolves else "villageois"
            self.players[socket]["role"] = role
            
            # Envoie le rôle au joueur
            role_message = {
                "type": "role_assignment",
                "role": role
            }
            self.send_message_to_player(socket, role_message)

    def remove_player(self, client_socket: socket.socket) -> None:
        """Retire un joueur de la partie"""
        if client_socket in self.players:
            player_name = self.players[client_socket]["name"]  # Accès correct au nom du joueur
            del self.players[client_socket]
            self.broadcast_system_message(f"{player_name} a quitté la partie.")
            self.broadcast_player_list()
            
            # Si la partie est en cours, on vérifie s'il faut mettre à jour le tour
            if self.started and client_socket == self.current_turn:
                if self.players:  # S'il reste des joueurs
                    self.current_turn = list(self.players.keys())[0]
                    self.broadcast_game_state()

    def broadcast_message(self, message: dict) -> None:
        """Envoie un message à tous les joueurs de la room"""
        for client_socket in self.players.keys():
            try:
                client_socket.send(json.dumps(message).encode())
            except Exception as e:
                print(f"Erreur d'envoi: {str(e)}")

    def broadcast_system_message(self, content: str) -> None:
        """Envoie un message système à tous les joueurs"""
        message = {
            "type": "chat",
            "player": "Système",
            "content": content
        }
        self.broadcast_message(message)

    def broadcast_player_list(self) -> None:
        """Envoie la liste mise à jour des joueurs à tous les participants"""
        # Extraction juste des noms des joueurs
        player_names = [player["name"] for player in self.players.values()]
    
        message = {
            "type": "player_list",
            "players": player_names  # On envoie juste la liste des noms
        }
        self.broadcast_message(message)

    def start_game(self, initiator_socket: socket.socket) -> bool:
        """Démarre la partie"""
        if self.started:
            return False
            
        if len(self.players) < self.min_players:
            self.send_message_to_player(initiator_socket, {
                "type": "error",
                "content": f"Il faut au moins {self.min_players} joueurs pour démarrer"
            })
            return False

        self.started = True
        self.assign_roles()
        
        # Initialise les positions des joueurs
        for socket, player in self.players.items():
            self.game_logic.add_player(player["name"], player["role"])

        # Définit le premier joueur
        self.current_turn = list(self.players.keys())[0]
        
        # Annonce le début de la partie
        self.broadcast_system_message("La partie commence !")
        self.broadcast_game_state()
        return True

    def broadcast_game_state(self):
        """Envoie l'état du jeu à chaque joueur"""
        current_player_name = self.players[self.current_turn]["name"] if self.current_turn else "Personne"
        
        for socket, player in self.players.items():
            player_name = player["name"]
            player_status = self.game_logic.players[player_name]['status']
            environment = self.game_logic.get_environment(player_name)
            state_message = {
                "type": "game_state",
                "environment": environment,
                "is_your_turn": socket == self.current_turn,
                "player_status": player_status,
                "current_player": current_player_name
            }
            self.send_message_to_player(socket, state_message)

    def handle_move(self, client_socket: socket.socket, direction: int):
        """Gère les déplacements des joueurs"""
        if not self.started or client_socket != self.current_turn:
            return
                
        player = self.players[client_socket]
        if self.game_logic.move_player(player["name"], direction):
            # Vérifie si un joueur est mort après le mouvement
            for name, player_info in self.game_logic.players.items():
                if player_info['status'] == 'dead' and name not in self.announced_deaths:
                    self.broadcast_system_message(f"{name} a été tué par un loup-garou!")
                    self.announced_deaths.add(name)  # Ajoute à la liste des morts annoncées

            # Passe au joueur suivant
            player_sockets = list(self.players.keys())
            current_index = player_sockets.index(client_socket)
            
            # Trouve le prochain joueur vivant
            next_player_found = False
            while not next_player_found:
                current_index = (current_index + 1) % len(player_sockets)
                next_socket = player_sockets[current_index]
                next_player = self.players[next_socket]
                if self.game_logic.players[next_player["name"]]['status'] == 'alive':
                    next_player_found = True
                    self.current_turn = next_socket
            
            # Met à jour l'état pour tous les joueurs
            self.broadcast_game_state()

    def send_message_to_player(self, client_socket: socket.socket, message: dict):
        """Envoie un message à un joueur spécifique"""
        try:
            client_socket.send(json.dumps(message).encode())
        except Exception as e:
            print(f"Erreur d'envoi: {str(e)}")

class GameServer:
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rooms: Dict[str, GameRoom] = {}
        self.client_room: Dict[socket.socket, str] = {}  # socket -> game_id

    def start(self):
        """Démarre le serveur"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Serveur démarré sur {self.host}:{self.port}")

        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Nouvelle connexion de {address}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket: socket.socket):
        """Gère les connexions individuelles des clients"""
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                message = json.loads(data)
                self.process_message(client_socket, message)

        except Exception as e:
            print(f"Erreur de connexion: {str(e)}")
        finally:
            self.disconnect_client(client_socket)

    def process_message(self, client_socket: socket.socket, message: dict):
        """Traite les messages reçus des clients"""
        message_type = message.get("type")
        game_id = message.get("game_id")

        if message_type == "connection":
            self.handle_connection(client_socket, message)
        elif message_type == "start_game":
            self.handle_start_game(client_socket, game_id)
        elif message_type == "message":
            self.handle_chat_message(client_socket, message)
        elif message_type == "move":
            self.handle_move(client_socket, message)
        elif message_type == "disconnect":
            self.handle_disconnect(client_socket, message)

    def handle_start_game(self, client_socket: socket.socket, game_id: str):
        """Gère la demande de démarrage de partie"""
        if game_id in self.rooms:
            room = self.rooms[game_id]
            room.start_game(client_socket)

    def handle_disconnect(self, client_socket: socket.socket, message: dict):
        """Gère la déconnexion volontaire d'un client"""
        self.disconnect_client(client_socket)

    def disconnect_client(self, client_socket: socket.socket):
        """Gère la déconnexion d'un client"""
        try:
            if client_socket in self.client_room:
                game_id = self.client_room[client_socket]
                room = self.rooms.get(game_id)
                if room:
                    # Récupérer le nom du joueur avant de le supprimer
                    player_name = room.players.get(client_socket, "Un joueur")
                    room.remove_player(client_socket)
                    if not room.players:  # Si la room est vide
                        del self.rooms[game_id]
                del self.client_room[client_socket]
        finally:
            client_socket.close()

    def handle_connection(self, client_socket: socket.socket, message: dict):
        """Gère les nouvelles connexions"""
        game_id = message.get("game_id")
        player_name = message.get("name")

        if game_id not in self.rooms:
            self.rooms[game_id] = GameRoom(game_id)

        room = self.rooms[game_id]
        # Plus de rôle à la connexion
        room.add_player(client_socket, player_name)
        self.client_room[client_socket] = game_id

        room.broadcast_system_message(f"{player_name} a rejoint la partie!")

    def handle_chat_message(self, client_socket: socket.socket, message: dict):
        """Gère les messages de chat"""
        game_id = message.get("game_id")
        if game_id in self.rooms:
            room = self.rooms[game_id]
            chat_message = {
                "type": "chat",
                "player": message.get("player"),
                "content": message.get("content")
            }
            room.broadcast_message(chat_message)

    def disconnect_client(self, client_socket: socket.socket):
        """Gère la déconnexion d'un client"""
        if client_socket in self.client_room:
            game_id = self.client_room[client_socket]
            room = self.rooms.get(game_id)
            if room:
                room.remove_player(client_socket)
                if not room.players:  # Si la room est vide
                    del self.rooms[game_id]
            del self.client_room[client_socket]
        client_socket.close()

    def handle_move(self, client_socket: socket.socket, message: dict):
        """Gère les déplacements des joueurs"""
        game_id = message.get("game_id")
        direction = message.get("direction")
        
        if game_id in self.rooms:
            room = self.rooms[game_id]
            room.handle_move(client_socket, direction)

if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")