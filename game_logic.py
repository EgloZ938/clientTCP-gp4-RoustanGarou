import random
from typing import Dict, List, Tuple

class GameLogic:
    def __init__(self, size: int = 7):  # Changé de 10 à 7
        self.size = size
        # Création de la grille avec des murs sur les bords
        self.grid = []
        for y in range(size):
            row = []
            for x in range(size):
                # Si on est sur un bord, on met un mur
                if x == 0 or x == size-1 or y == 0 or y == size-1:
                    row.append('#')
                else:
                    row.append(' ')
            self.grid.append(row)
        self.players: Dict[str, dict] = {}
        self.current_turn = None
        self.game_started = False

    def add_player(self, player_name: str, role: str) -> bool:
        """Ajoute un joueur à la partie"""
        if player_name in self.players:
            return False
            
        # Place le joueur aléatoirement sur la grille
        x, y = self.get_random_empty_position()
        self.players[player_name] = {
            'position': (x, y),
            'role': role,
            'status': 'alive'
        }
        self.grid[y][x] = 'L' if role == 'loup' else 'V'
        return True

    def get_random_empty_position(self) -> Tuple[int, int]:
        """Trouve une position vide aléatoire sur la grille"""
        empty_positions = [
            (x, y) for x in range(self.size)
            for y in range(self.size)
            if self.grid[y][x] == ' '
        ]
        return random.choice(empty_positions)

    def move_player(self, player_name: str, direction: int) -> bool:
        """Déplace un joueur dans une direction"""
        if player_name not in self.players or self.players[player_name].get('status') == 'dead':
            return False

        x, y = self.players[player_name]['position']
        new_x, new_y = self.get_new_position(x, y, direction)

        if self.is_valid_move(new_x, new_y, player_name):  # Ajout de player_name
            # Vérifie s'il y a une collision avec un autre joueur
            for other_name, other_player in self.players.items():
                if other_name != player_name:
                    other_x, other_y = other_player['position']
                    if (new_x, new_y) == (other_x, other_y):
                        # Si un loup rencontre un villageois
                        if self.players[player_name]['role'] == 'loup' and \
                        other_player['role'] == 'villageois' and \
                        other_player['status'] == 'alive':
                            other_player['status'] = 'dead'
                            # On enlève le villageois mort de la grille
                            self.grid[other_y][other_x] = ' '
                            # On efface l'ancienne position du loup
                            self.grid[y][x] = ' '
                            # On déplace le loup sur la position du villageois mort
                            self.grid[new_y][new_x] = 'L'
                            self.players[player_name]['position'] = (new_x, new_y)
                            return True

            # Si pas de collision, mouvement normal
            self.grid[y][x] = ' '
            if self.players[player_name]['status'] == 'alive':
                self.grid[new_y][new_x] = 'L' if self.players[player_name]['role'] == 'loup' else 'V'
            self.players[player_name]['position'] = (new_x, new_y)
            return True

        return False

    def get_new_position(self, x: int, y: int, direction: int) -> Tuple[int, int]:
        """Calcule la nouvelle position selon la direction"""
        directions = {
            1: (0, -1),   # haut
            2: (0, 1),    # bas
            3: (-1, 0),   # gauche
            4: (1, 0),    # droite
            5: (-1, -1),  # haut-gauche
            6: (1, -1),   # haut-droite
            7: (1, 1),    # bas-droite
            8: (-1, 1)    # bas-gauche
        }
        dx, dy = directions.get(direction, (0, 0))
        return (x + dx, y + dy)

    def is_valid_move(self, x: int, y: int, player_name: str) -> bool:  # Ajout de player_name comme paramètre
        """Vérifie si un déplacement est valide"""
        # Vérifie d'abord les limites et les murs
        if not (0 <= x < self.size and 0 <= y < self.size and self.grid[y][x] != '#'):
            return False

        # Vérifie les collisions avec d'autres joueurs
        player = self.players[player_name]
        if player['role'] != 'loup':  # Si ce n'est pas un loup
            # Vérifie si la case est occupée par un autre joueur
            for other_name, other_player in self.players.items():
                if other_name != player_name:  # Ne pas se compter soi-même
                    other_x, other_y = other_player['position']
                    if (x, y) == (other_x, other_y) and other_player['status'] == 'alive':
                        return False  # Case occupée, mouvement invalide pour un villageois

        return True  # Si toutes les vérifications sont passées, le mouvement est valide

    def get_environment(self, player_name: str) -> List[str]:
        if player_name not in self.players:
            return []

        x, y = self.players[player_name]['position']
        role = self.players[player_name]['role']
        status = self.players[player_name].get('status', 'alive')  # Nouveau : status du joueur
        environment = []

        # Si le joueur est mort, il voit tout
        if status == 'dead':
            for i in range(self.size):
                for j in range(self.size):
                    environment.append(self.grid[i][j])
            return environment

        # On parcourt toute la grille
        for i in range(self.size):
            for j in range(self.size):
                # Position actuelle du joueur
                if i == y and j == x:
                    environment.append('P')
                    continue

                # Si c'est un mur, on le voit toujours
                if self.grid[i][j] == '#':
                    environment.append('#')
                    continue

                # Calcul de la distance Manhattan
                distance = abs(x - j) + abs(y - i)

                # Règles de vision selon le rôle
                if self.grid[i][j] in ['L', 'V']:
                    if (role == 'loup' and distance <= 2) or \
                    (role == 'villageois' and distance <= 1):
                        environment.append(self.grid[i][j])
                    else:
                        environment.append(' ')
                else:
                    environment.append(self.grid[i][j])

        return environment

    def can_start_game(self) -> bool:
        """Vérifie si la partie peut démarrer"""
        return len(self.players) >= 4  # Minimum 4 joueurs