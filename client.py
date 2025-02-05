import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json
from typing import List

class Connexion:
    def __init__(self, message_callback):
        self.socket = None
        self.connected = False
        self.message_callback = message_callback
        self.player_name = None
        self.game_id = None
        
    def connect(self, host, port, player_name, game_id):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            self.player_name = player_name
            self.game_id = game_id
            
            player_info = {
                "type": "connection",
                "name": player_name,
                "game_id": game_id
            }
            self.socket.send(json.dumps(player_info).encode())
            
            self.connected = True
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            return True, "Connecté au serveur!"
        except Exception as e:
            return False, str(e)
        
    def send_disconnect_message(self):
        """Envoie un message de déconnexion au serveur"""
        if self.connected and self.socket:
            try:
                disconnect_msg = {
                    "type": "disconnect",
                    "game_id": self.game_id,
                    "name": self.player_name
                }
                self.socket.send(json.dumps(disconnect_msg).encode())
            except:
                pass
            
    def send_message(self, player_name, game_id, content):
        if not self.connected:
            return False, "Non connecté au serveur"
            
        try:
            message = {
                "type": "message",
                "content": content,
                "game_id": game_id,
                "player": player_name
            }
            self.socket.send(json.dumps(message).encode())
            return True, None
        except Exception as e:
            return False, str(e)
            
    def receive_messages(self):
        """Reçoit et traite les messages du serveur"""
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                buffer += data
                
                # Traite tous les messages complets dans le buffer
                while True:
                    try:
                        # Trouve la première occurrence d'un message JSON complet
                        json_end = buffer.find('}') + 1
                        if json_end <= 0:
                            break
                            
                        message = json.loads(buffer[:json_end])
                        self.message_callback(message)
                        
                        # Retire le message traité du buffer
                        buffer = buffer[json_end:].strip()
                        
                    except json.JSONDecodeError:
                        # Si le message n'est pas un JSON complet, on attend plus de données
                        break
                    except Exception as e:
                        print(f"Erreur de traitement du message: {str(e)}")
                        break
                        
            except Exception as e:
                print(f"Erreur de réception: {str(e)}")
                self.connected = False
                break
                
    def cleanup(self):
        if self.connected:
            self.send_disconnect_message()
        if self.socket:
            self.connected = False
            self.socket.close()


class ClientApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Loup-Garou - Client")
        self.root.geometry("800x600")
        
        # Variables
        self.player_name = tk.StringVar()
        self.game_id = tk.StringVar()
        self.message_var = tk.StringVar()
        self.is_connected = False
        self.game_started = False
        self.game_ui = None
        
        # Initialisation du gestionnaire réseau
        self.network = Connexion(self.handle_message)
        
        # Gestion de la fermeture de fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_gui()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Section connexion
        connection_frame = ttk.Frame(main_frame)
        connection_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(connection_frame, text="Nom du joueur:").grid(row=0, column=0, pady=5)
        ttk.Entry(connection_frame, textvariable=self.player_name).grid(row=0, column=1, pady=5)
        
        ttk.Label(connection_frame, text="ID Partie:").grid(row=1, column=0, pady=5)
        ttk.Entry(connection_frame, textvariable=self.game_id).grid(row=1, column=1, pady=5)
        
        self.connect_button = ttk.Button(connection_frame, text="Connexion", command=self.connect_to_server)
        self.connect_button.grid(row=2, column=0, pady=10)
        
        self.disconnect_button = ttk.Button(connection_frame, text="Déconnexion", command=self.disconnect_from_server, state='disabled')
        self.disconnect_button.grid(row=2, column=1, pady=10)
        
        # Bouton démarrer partie
        self.start_game_button = ttk.Button(connection_frame, text="Démarrer la partie", command=self.send_start_game, state='disabled')
        self.start_game_button.grid(row=2, column=2, pady=10, padx=5)
        
        # Zone de chat et jeu
        self.chat_frame = ttk.Frame(main_frame)
        self.chat_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Zone de chat
        self.chat_text = tk.Text(self.chat_frame, height=20, width=50, state='disabled')
        self.chat_text.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Liste des joueurs
        ttk.Label(main_frame, text="Joueurs connectés:").grid(row=2, column=2, padx=10)
        self.players_list = tk.Listbox(main_frame, height=10, width=20)
        self.players_list.grid(row=3, column=2, padx=10, rowspan=2)
        
        # Zone de saisie message
        self.message_entry = ttk.Entry(self.chat_frame, textvariable=self.message_var, state='disabled')
        self.message_entry.grid(row=1, column=0, pady=5)
        self.send_button = ttk.Button(self.chat_frame, text="Envoyer", command=self.send_message, state='disabled')
        self.send_button.grid(row=1, column=1, pady=5)
        

    def send_start_game(self):
        """Envoie la demande de démarrage de partie"""
        if self.is_connected:
            message = {
                "type": "start_game",
                "game_id": self.game_id.get()
            }
            self.network.socket.send(json.dumps(message).encode())

    def connect_to_server(self):
        if not self.player_name.get() or not self.game_id.get():
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
            
        success, message = self.network.connect(
            'localhost', 
            12345, 
            self.player_name.get(), 
            self.game_id.get()
        )
        
        if success:
            self.is_connected = True
            self.add_message(message)
            self.update_connection_state()
        else:
            messagebox.showerror("Erreur de connexion", message)

    def disconnect_from_server(self):
        if self.is_connected:
            self.network.cleanup()
            self.is_connected = False
            self.update_connection_state()
            self.players_list.delete(0, tk.END)
            self.add_message("Déconnecté du serveur")

    def update_connection_state(self):
        """Met à jour l'état des boutons selon la connexion"""
        if self.is_connected:
            self.connect_button.configure(state='disabled')
            self.disconnect_button.configure(state='normal')
            self.message_entry.configure(state='normal')
            self.send_button.configure(state='normal')
        else:
            self.connect_button.configure(state='normal')
            self.disconnect_button.configure(state='disabled')
            self.message_entry.configure(state='disabled')
            self.send_button.configure(state='disabled')

    def on_closing(self):
        """Gère la fermeture propre de l'application"""
        if self.is_connected:
            self.disconnect_from_server()
        self.root.destroy()
            
    def send_message(self):
        if not self.message_var.get():
            return
            
        success, error = self.network.send_message(
            self.player_name.get(),
            self.game_id.get(),
            self.message_var.get()
        )
        
        if success:
            self.message_var.set("")
        else:
            self.add_message(f"Erreur d'envoi: {error}")
            
    def handle_message(self, message):
        """Gère les différents types de messages reçus"""
        msg_type = message.get("type")
        
        if msg_type == "player_list":
            players = message.get("players", [])
            self.update_players_list(players)
            # Active le bouton démarrer si assez de joueurs (4+)
            self.start_game_button.configure(state='normal' if len(players) >= 4 else 'disabled')
            
        elif msg_type == "chat":
            self.add_message(f"{message.get('player')}: {message.get('content')}")
            
        elif msg_type == "role_assignment":
            self.handle_role_assignment(message)
            
        elif msg_type == "game_state":
            self.handle_game_state(message)
            
        elif msg_type == "error":
            messagebox.showerror("Erreur", message.get("content"))
            

    def handle_game_state(self, message):
        """Gère les mises à jour d'état du jeu"""
        if not self.game_started:
            self.start_game_ui()
            
        environment = message.get("environment", [])
        is_your_turn = message.get("is_your_turn", False)
        
        self.game_ui.update_grid(environment)
        self.game_ui.set_move_enabled(is_your_turn)
    

    def start_game_ui(self):
        """Initialise l'interface de jeu"""
        self.game_started = True
        self.start_game_button.configure(state='disabled')
        
        # Crée la frame de jeu
        game_frame = ttk.Frame(self.root)
        game_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10)
        
        self.game_ui = GameUI(game_frame)
        self.game_ui.on_move = self.send_move

    def send_move(self, direction: int):
        """Envoie un mouvement au serveur"""
        if self.is_connected:
            message = {
                "type": "move",
                "direction": direction,
                "game_id": self.game_id.get()
            }
            self.network.socket.send(json.dumps(message).encode())

    def add_message(self, message):
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, message + "\n")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
    def update_game_status(self, status):
        # À implémenter selon les besoins
        pass
        
    def handle_role_assignment(self, message):
        """Gère l'attribution du rôle"""
        role = message.get("role")
        messagebox.showinfo("Attribution du rôle", f"Vous êtes un {role}")
        # Active l'interface de jeu après l'attribution du rôle
        if not self.game_started:
            self.start_game_ui()
        
    def run(self):
        self.root.mainloop()
        
    def cleanup(self):
        self.network.cleanup()

    def update_players_list(self, players):
        self.players_list.delete(0, tk.END)
        for player in players:
            self.players_list.insert(tk.END, player)


class GameUI:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid()
        self.grid_cells = []
        self.setup_ui()

    def setup_ui(self):
        # Grille de jeu (5x5 pour supporter la vision du loup)
        grid_frame = ttk.Frame(self.frame)
        grid_frame.grid(row=0, column=0, padx=10, pady=10)

        # Style pour les cellules
        style = ttk.Style()
        style.configure('Cell.TLabel', font=('TkDefaultFont', 12, 'bold'), padding=5)

        self.grid_cells = []
        for i in range(5):
            row = []
            for j in range(5):
                cell = ttk.Label(
                    grid_frame, 
                    text='', 
                    width=3, 
                    style='Cell.TLabel',
                    borderwidth=1, 
                    relief="solid"
                )
                cell.grid(row=i, column=j, padx=1, pady=1)
                row.append(cell)
            self.grid_cells.append(row)

        # Boutons de contrôle
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=1, column=0, pady=10)

        # Directions: haut, bas, gauche, droite, diagonales
        directions = [
            (0, 0, "↖", 5), (0, 1, "↑", 1), (0, 2, "↗", 6),
            (1, 0, "←", 3), (1, 1, "•", 0), (1, 2, "→", 4),
            (2, 0, "↙", 8), (2, 1, "↓", 2), (2, 2, "↘", 7)
        ]

        for row, col, symbol, direction in directions:
            if direction != 0:  # Skip center button
                btn = ttk.Button(
                    control_frame,
                    text=symbol,
                    width=3,
                    command=lambda d=direction: self.on_move(d)
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

    def update_grid(self, environment: List[str]):
        """Met à jour l'affichage de la grille"""
        symbols = {
            'L': 'L',    # Loup
            'V': 'V',    # Villageois
            'P': 'P',    # Joueur (Player)
            ' ': '.',    # Case vide
            'X': '#'     # Hors limites/invisible
        }
        
        size = 5  # Taille de la grille d'affichage
        for i in range(size):
            for j in range(size):
                index = i * size + j
                if index < len(environment):
                    symbol = symbols.get(environment[index], '?')
                    # Configuration des couleurs selon le type
                    if symbol == 'L':
                        cell_style = {'foreground': 'red'}
                    elif symbol == 'V':
                        cell_style = {'foreground': 'blue'}
                    elif symbol == 'P':
                        cell_style = {'foreground': 'green'}
                    else:
                        cell_style = {'foreground': 'black'}
                    
                    self.grid_cells[i][j].configure(text=symbol, **cell_style)

    def set_move_enabled(self, enabled: bool):
        """Active/désactive les boutons de mouvement"""
        for widgets in self.frame.winfo_children():
            for widget in widgets.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.configure(state='normal' if enabled else 'disabled')

    def on_move(self, direction: int):
        """À implémenter dans la classe principale pour gérer les mouvements"""
        pass

if __name__ == "__main__":
    app = ClientApp()
    try:
        app.run()
    finally:
        app.cleanup()