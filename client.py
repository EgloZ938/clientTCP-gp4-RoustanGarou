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
        # Frame principale
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configure les poids des lignes et colonnes
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Section connexion (en haut)
        connection_frame = ttk.Frame(self.main_frame)
        connection_frame.grid(row=0, column=0, columnspan=3, pady=5, sticky='ew')
        
        ttk.Label(connection_frame, text="Nom du joueur:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(connection_frame, textvariable=self.player_name).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(connection_frame, text="ID Partie:").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(connection_frame, textvariable=self.game_id).grid(row=0, column=3, padx=5, pady=5)
        
        button_frame = ttk.Frame(connection_frame)
        button_frame.grid(row=0, column=4, padx=5, pady=5)
        
        self.connect_button = ttk.Button(button_frame, text="Connexion", command=self.connect_to_server)
        self.connect_button.pack(side='left', padx=2)
        
        self.disconnect_button = ttk.Button(button_frame, text="Déconnexion", 
                                          command=self.disconnect_from_server, state='disabled')
        self.disconnect_button.pack(side='left', padx=2)
        
        self.start_game_button = ttk.Button(button_frame, text="Démarrer la partie",
                                          command=self.send_start_game, state='disabled')
        self.start_game_button.pack(side='left', padx=2)
        
        # Création d'un canvas scrollable pour le contenu principal
        canvas = tk.Canvas(self.main_frame)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Zone de jeu (sera visible quand la partie démarre)
        self.game_frame = ttk.Frame(self.scrollable_frame)
        self.game_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Zone de chat et liste des joueurs
        chat_section = ttk.Frame(self.scrollable_frame)
        chat_section.grid(row=1, column=0, padx=10, pady=5)
        
        # Zone de chat
        self.chat_text = tk.Text(chat_section, height=20, width=50, state='disabled')
        self.chat_text.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Zone de saisie message
        self.message_entry = ttk.Entry(chat_section, textvariable=self.message_var, state='disabled')
        self.message_entry.grid(row=1, column=0, pady=5)
        self.send_button = ttk.Button(chat_section, text="Envoyer", 
                                    command=self.send_message, state='disabled')
        self.send_button.grid(row=1, column=1, pady=5)
        
        # Liste des joueurs
        players_section = ttk.Frame(self.scrollable_frame)
        players_section.grid(row=1, column=2, padx=10, pady=5)
        
        ttk.Label(players_section, text="Joueurs connectés:").grid(row=0, column=0)
        self.players_list = tk.Listbox(players_section, height=10, width=20)
        self.players_list.grid(row=1, column=0)
        
        # Configuration du scroll
        canvas.grid(row=1, column=0, columnspan=3, sticky="nsew")
        scrollbar.grid(row=1, column=3, sticky="ns")
        
        # Configuration des poids pour le redimensionnement
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
    def handle_role_assignment(self, message):
        """Gère l'attribution du rôle"""
        role = message.get("role")
        messagebox.showinfo("Attribution du rôle", f"Vous êtes un {role}")
        
        # Active l'interface de jeu après l'attribution du rôle
        if not self.game_started:
            self.start_game_ui()
        
        # Met à jour l'affichage du rôle
        if self.game_ui:
            self.game_ui.set_role(role)  # Cette ligne met à jour l'affichage du rôle

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
        player_status = message.get("player_status", "alive")
        
        # Mise à jour du status
        if self.game_ui:
            self.game_ui.set_status(player_status)
            self.game_ui.update_grid(environment)
            self.game_ui.set_move_enabled(is_your_turn and player_status == 'alive')

    def start_game_ui(self):
        """Initialise l'interface de jeu"""
        self.game_started = True
        self.start_game_button.configure(state='disabled')
        
        # Créer l'interface de jeu dans la frame dédiée
        if self.game_ui is None:
            self.game_ui = GameUI(self.game_frame)
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
        self.role_label = None
        self.setup_ui()

    def setup_ui(self):
        # Container pour la grille et le rôle
        container = ttk.Frame(self.frame)
        container.grid(row=0, column=0, padx=10, pady=10)

        # Grille de jeu (7x7)
        grid_frame = ttk.Frame(container)
        grid_frame.grid(row=0, column=0, padx=10, pady=10)

        # Style pour les cellules
        style = ttk.Style()
        style.configure('Cell.TLabel', font=('TkDefaultFont', 12, 'bold'), padding=5)

        # Création de la grille 7x7
        self.grid_cells = []
        for i in range(7):  # Changé de 5 à 7
            row = []
            for j in range(7):  # Changé de 5 à 7
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

        # Nouveau : Frame pour le rôle
        role_frame = ttk.Frame(container)
        role_frame.grid(row=0, column=1, padx=10, pady=10, sticky='n')
        
        ttk.Label(role_frame, text="Votre rôle:", font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=0, pady=(0,5))
        self.role_label = ttk.Label(role_frame, text="Non défini", font=('TkDefaultFont', 11))
        self.role_label.grid(row=1, column=0)

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
        'P': 'P',    # Joueur
        ' ': '.',    # Case vide
        '#': '■',    # Mur
        'X': ' '     # Hors limites
        }
        
        size = 7
        for i in range(size):
            for j in range(size):
                index = i * size + j
                if index < len(environment):
                    symbol = symbols.get(environment[index], '?')
                    
                    if symbol == 'L':
                        cell_style = {'foreground': 'red', 'text': symbol}
                    elif symbol == 'V':
                        cell_style = {'foreground': 'blue', 'text': symbol}
                    elif symbol == 'P':
                        if self.role_label.cget("text") == "Mort":
                            cell_style = {'foreground': 'gray', 'text': '†'}
                        else:
                            cell_style = {'foreground': 'green', 'text': symbol}
                    elif symbol == '■':
                        cell_style = {'foreground': 'black', 'text': symbol}
                    elif symbol == '.':
                        cell_style = {'foreground': 'grey', 'text': symbol}
                    else:
                        cell_style = {'foreground': 'black', 'text': symbol}
                    
                    self.grid_cells[i][j].configure(**cell_style)

    def set_status(self, status: str):
        """Met à jour le status du joueur"""
        if status == "dead":
            self.role_label.configure(text="MORT", foreground='gray')

    def set_role(self, role: str):
        """Met à jour l'affichage du rôle"""
        if role == "loup":
            self.role_label.configure(text="Loup-Garou", foreground='red')
        else:
            self.role_label.configure(text="Villageois", foreground='blue')

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