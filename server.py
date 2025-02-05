import socket
import threading
import json
from typing import Dict, List

class GameRoom:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players: Dict[socket.socket, str] = {}  # socket -> player_name
        self.messages: List[dict] = []
        self.started = False

    def add_player(self, client_socket: socket.socket, player_name: str) -> None:
        self.players[client_socket] = player_name
        self.broadcast_player_list()

    def remove_player(self, client_socket: socket.socket) -> None:
        if client_socket in self.players:
            player_name = self.players[client_socket]
            del self.players[client_socket]
            self.broadcast_system_message(f"{player_name} a quitté la partie.")
            self.broadcast_player_list()

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
        message = {
            "type": "player_list",
            "players": list(self.players.values())
        }
        self.broadcast_message(message)

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
        elif message_type == "message":
            self.handle_chat_message(client_socket, message)

    def handle_connection(self, client_socket: socket.socket, message: dict):
        """Gère les nouvelles connexions"""
        game_id = message.get("game_id")
        player_name = message.get("name")

        # Crée la room si elle n'existe pas
        if game_id not in self.rooms:
            self.rooms[game_id] = GameRoom(game_id)

        room = self.rooms[game_id]
        room.add_player(client_socket, player_name)
        self.client_room[client_socket] = game_id

        # Annonce l'arrivée du nouveau joueur
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

if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")