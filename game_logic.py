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
            'role': role
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
        """Déplace un joueur dans une direction donnée"""
        if player_name not in self.players:
            return False

        x, y = self.players[player_name]['position']
        new_x, new_y = self.get_new_position(x, y, direction)

        if self.is_valid_move(new_x, new_y):
            # Efface l'ancienne position
            self.grid[y][x] = ' '
            # Met à jour la nouvelle position
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

    def is_valid_move(self, x: int, y: int) -> bool:
        """Vérifie si un déplacement est valide"""
        return (0 <= x < self.size and
                0 <= y < self.size and
                self.grid[y][x] != '#')

    def get_environment(self, player_name: str) -> List[str]:
        """Retourne l'environnement visible d'un joueur"""
        if player_name not in self.players:
            return []

        x, y = self.players[player_name]['position']
        role = self.players[player_name]['role']
        environment = []

        # On parcourt toute la grille pour voir les murs (#)
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
                    if role == 'loup' and distance <= 1:
                        # Le loup voit les joueurs à distance 1
                        environment.append(self.grid[i][j])
                    elif role == 'villageois' and distance <= 2:
                        # Les villageois voient à distance 2
                        environment.append(self.grid[i][j])
                    else:
                        environment.append(' ')
                else:
                    environment.append(self.grid[i][j])

        return environment

    def can_start_game(self) -> bool:
        """Vérifie si la partie peut démarrer"""
        return len(self.players) >= 4  # Minimum 4 joueurs