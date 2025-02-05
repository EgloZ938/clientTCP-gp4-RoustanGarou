import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json

class LoupGarouClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Loup-Garou - Client")
        self.root.geometry("800x600")
        
        # Variables de connexion
        self.socket = None
        self.connected = False
        self.player_name = tk.StringVar()
        self.game_id = tk.StringVar()
        
        self.setup_gui()
        
    def setup_gui(self):
        # Frame principale
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
        
        # Zone de saisie message
        self.message_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.message_var).grid(row=4, column=0, pady=5)
        ttk.Button(main_frame, text="Envoyer", command=self.send_message).grid(row=4, column=1, pady=5)
        
    def connect_to_server(self):
        if not self.player_name.get() or not self.game_id.get():
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 12345))  # Adapter le port selon votre serveur
            
            # Envoyer les informations du joueur
            player_info = {
                "type": "connection",
                "name": self.player_name.get(),
                "game_id": self.game_id.get()
            }
            self.socket.send(json.dumps(player_info).encode())
            
            # Démarrer le thread d'écoute
            self.connected = True
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.add_message("Connecté au serveur!")
            
        except Exception as e:
            messagebox.showerror("Erreur de connexion", str(e))
            
    def send_message(self):
        if not self.connected or not self.message_var.get():
            return
            
        try:
            message = {
                "type": "message",
                "content": self.message_var.get(),
                "game_id": self.game_id.get(),
                "player": self.player_name.get()
            }
            self.socket.send(json.dumps(message).encode())
            self.message_var.set("")  # Vider le champ de message
            
        except Exception as e:
            self.add_message(f"Erreur d'envoi: {str(e)}")
            
    def receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if data:
                    message = json.loads(data)
                    self.handle_message(message)
            except Exception as e:
                print(f"Erreur de réception: {str(e)}")
                self.connected = False
                break
                
    def handle_message(self, message):
        """Gère les différents types de messages reçus du serveur"""
        if message.get("type") == "game_status":
            self.update_game_status(message)
        elif message.get("type") == "chat":
            self.add_message(f"{message.get('player')}: {message.get('content')}")
        elif message.get("type") == "role_assignment":
            self.handle_role_assignment(message)
            
    def add_message(self, message):
        """Ajoute un message à la zone de chat"""
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, message + "\n")
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
        
    def update_game_status(self, status):
        """Met à jour l'état du jeu dans l'interface"""
        # À implémenter selon les besoins
        pass
        
    def handle_role_assignment(self, message):
        """Gère l'attribution des rôles"""
        role = message.get("role")
        messagebox.showinfo("Attribution du rôle", f"Vous êtes un {role}")
        
    def run(self):
        self.root.mainloop()
        
    def cleanup(self):
        """Nettoie les ressources avant de fermer"""
        if self.socket:
            self.socket.close()
        
if __name__ == "__main__":
    client = LoupGarouClient()
    try:
        client.run()
    finally:
        client.cleanup()