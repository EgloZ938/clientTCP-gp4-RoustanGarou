import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json

class Connexion:
    def __init__(self, message_callback):
        self.socket = None
        self.connected = False
        self.message_callback = message_callback
        
    def connect(self, host, port, player_name, game_id):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
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
        while self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if data:
                    message = json.loads(data)
                    self.message_callback(message)
            except Exception as e:
                print(f"Erreur de réception: {str(e)}")
                self.connected = False
                break
                
    def cleanup(self):
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
        
        # Initialisation du gestionnaire réseau
        self.network = Connexion(self.handle_message)
        
        self.setup_gui()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Section connexion
        ttk.Label(main_frame, text="Nom du joueur:").grid(row=0, column=0, pady=5)
        ttk.Entry(main_frame, textvariable=self.player_name).grid(row=0, column=1, pady=5)
        
        ttk.Label(main_frame, text="ID Partie:").grid(row=1, column=0, pady=5)
        ttk.Entry(main_frame, textvariable=self.game_id).grid(row=1, column=1, pady=5)
        
        ttk.Button(main_frame, text="Connexion", command=self.connect_to_server).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Zone de chat
        self.chat_text = tk.Text(main_frame, height=20, width=50, state='disabled')
        self.chat_text.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Liste des joueurs
        ttk.Label(main_frame, text="Joueurs connectés:").grid(row=2, column=2, padx=10)
        self.players_list = tk.Listbox(main_frame, height=10, width=20)
        self.players_list.grid(row=3, column=2, padx=10, rowspan=2)
        
        # Zone de saisie message
        ttk.Entry(main_frame, textvariable=self.message_var).grid(row=4, column=0, pady=5)
        ttk.Button(main_frame, text="Envoyer", command=self.send_message).grid(row=4, column=1, pady=5)
        
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
            self.add_message(message)
        else:
            messagebox.showerror("Erreur de connexion", message)
            
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
        if message.get("type") == "player_list":
            self.update_players_list(message.get("players", []))
        elif message.get("type") == "chat":
            self.add_message(f"{message.get('player')}: {message.get('content')}")
        elif message.get("type") == "role_assignment":
            self.handle_role_assignment(message)
            
    def add_message(self, message):
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, message + "\n")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
    def update_game_status(self, status):
        # À implémenter selon les besoins
        pass
        
    def handle_role_assignment(self, message):
        role = message.get("role")
        messagebox.showinfo("Attribution du rôle", f"Vous êtes un {role}")
        
    def run(self):
        self.root.mainloop()
        
    def cleanup(self):
        self.network.cleanup()

    def update_players_list(self, players):
        self.players_list.delete(0, tk.END)
        for player in players:
            self.players_list.insert(tk.END, player)

if __name__ == "__main__":
    app = ClientApp()
    try:
        app.run()
    finally:
        app.cleanup()