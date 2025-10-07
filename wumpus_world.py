
import random

class WumpusWorld:
    def __init__(self, size=4, num_pits=3, num_wumpus=1):
        self.size = size
        self.grid = [['.' for _ in range(size)] for _ in range(size)]
        self.hunter_pos = (0, 0)  # Start at (0,0)
        self.wumpus_pos = None
        self.gold_pos = None
        self.pits_pos = []
        self.has_gold = False
        self.has_arrow = True
        self.is_alive = True
        self.score = 0
        self.game_over = False

        self._place_elements(num_pits, num_wumpus)
        self._update_percepts()

    def _place_elements(self, num_pits, num_wumpus):
        # Place Wumpus
        while self.wumpus_pos is None or self.wumpus_pos == self.hunter_pos:
            self.wumpus_pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
        self.grid[self.wumpus_pos[0]][self.wumpus_pos[1]] = 'W'

        # Place Gold
        while self.gold_pos is None or self.gold_pos == self.hunter_pos or self.gold_pos == self.wumpus_pos:
            self.gold_pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
        self.grid[self.gold_pos[0]][self.gold_pos[1]] = 'G'

        # Place Pits
        for _ in range(num_pits):
            pit_pos = None
            while pit_pos is None or pit_pos == self.hunter_pos or pit_pos == self.wumpus_pos or pit_pos == self.gold_pos or pit_pos in self.pits_pos:
                pit_pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
            self.pits_pos.append(pit_pos)
            self.grid[pit_pos[0]][pit_pos[1]] = 'P'

    def _get_neighbors(self, r, c):
        neighbors = []
        if r > 0: neighbors.append((r - 1, c))
        if r < self.size - 1: neighbors.append((r + 1, c))
        if c > 0: neighbors.append((r, c - 1))
        if c < self.size - 1: neighbors.append((r, c + 1))
        return neighbors

    def _update_percepts(self):
        # Clear old percepts
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] not in ['W', 'G', 'P', 'H']:
                    self.grid[r][c] = '.'

        # Add new percepts
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) == self.wumpus_pos:
                    for nr, nc in self._get_neighbors(r, c):
                        if self.grid[nr][nc] == '.':
                            self.grid[nr][nc] = 'S'  # Stench
                        elif self.grid[nr][nc] == 'B': # If already Breeze, keep it
                            pass
                        else:
                            self.grid[nr][nc] += 'S'
                elif (r, c) in self.pits_pos:
                    for nr, nc in self._get_neighbors(r, c):
                        if self.grid[nr][nc] == '.':
                            self.grid[nr][nc] = 'B'  # Breeze
                        elif self.grid[nr][nc] == 'S': # If already Stench, keep it
                            pass
                        else:
                            self.grid[nr][nc] += 'B'
                elif (r, c) == self.gold_pos:
                    if self.grid[r][c] == '.':
                        self.grid[r][c] = 'L' # Glitter
                    else:
                        self.grid[r][c] += 'L'

        # Place hunter last to ensure it's visible
        self.grid[self.hunter_pos[0]][self.hunter_pos[1]] = 'H'

    def move_hunter(self, dr, dc):
        if self.game_over:
            return

        new_r, new_c = self.hunter_pos[0] + dr, self.hunter_pos[1] + dc

        if 0 <= new_r < self.size and 0 <= new_c < self.size:
            self.hunter_pos = (new_r, new_c)
            self.score -= 1 # Each move costs 1 point
            self._check_game_state()
            self._update_percepts()
        else:
            print("Movimento inválido: fora do tabuleiro.")

    def shoot_arrow(self, direction):
        if self.game_over or not self.has_arrow:
            return

        self.has_arrow = False
        self.score -= 10 # Shooting an arrow costs 10 points

        r, c = self.hunter_pos
        wumpus_killed = False

        if direction == 'up':
            for i in range(r - 1, -1, -1):
                if (i, c) == self.wumpus_pos:
                    wumpus_killed = True
                    break
        elif direction == 'down':
            for i in range(r + 1, self.size):
                if (i, c) == self.wumpus_pos:
                    wumpus_killed = True
                    break
        elif direction == 'left':
            for j in range(c - 1, -1, -1):
                if (r, j) == self.wumpus_pos:
                    wumpus_killed = True
                    break
        elif direction == 'right':
            for j in range(c + 1, self.size):
                if (r, j) == self.wumpus_pos:
                    wumpus_killed = True
                    break

        if wumpus_killed:
            print("Você matou o Wumpus!")
            self.grid[self.wumpus_pos[0]][self.wumpus_pos[1]] = '.' # Remove Wumpus from grid
            self.wumpus_pos = None
            self.score += 1000 # Bonus for killing Wumpus
            self._update_percepts() # Update percepts after Wumpus is gone
        else:
            print("Você errou o Wumpus.")

    def grab_gold(self):
        if self.game_over:
            return

        if self.hunter_pos == self.gold_pos and not self.has_gold:
            self.has_gold = True
            self.score += 1000 # Bonus for grabbing gold
            self.grid[self.gold_pos[0]][self.gold_pos[1]] = 'H' # Remove Glitter from grid
            print("Você pegou o ouro!")
            self._update_percepts()

    def climb_out(self):
        if self.game_over:
            return

        if self.hunter_pos == (0, 0) and self.has_gold:
            self.score += 1000 # Bonus for climbing out with gold
            self.game_over = True
            print("Você escapou com o ouro! Fim de jogo.")
        elif self.hunter_pos == (0, 0) and not self.has_gold:
            self.game_over = True
            print("Você escapou sem o ouro. Fim de jogo.")
        else:
            print("Você só pode escalar na posição inicial (0,0).")

    def _check_game_state(self):
        if self.hunter_pos == self.wumpus_pos and self.wumpus_pos is not None:
            self.is_alive = False
            self.game_over = True
            self.score -= 1000 # Penalty for dying
            print("Você foi comido pelo Wumpus! Fim de jogo.")
        elif self.hunter_pos in self.pits_pos:
            self.is_alive = False
            self.game_over = True
            self.score -= 1000 # Penalty for dying
            print("Você caiu em um poço! Fim de jogo.")

    def get_percepts(self, r, c):
        percepts = []
        if (r, c) == self.hunter_pos:
            if self.wumpus_pos is not None and self.hunter_pos == self.wumpus_pos:
                percepts.append('Wumpus')
            if self.hunter_pos in self.pits_pos:
                percepts.append('Pit')
            if self.hunter_pos == self.gold_pos and not self.has_gold:
                percepts.append('Glitter')

            # Check neighbors for Stench and Breeze
            for nr, nc in self._get_neighbors(r, c):
                if self.wumpus_pos is not None and (nr, nc) == self.wumpus_pos:
                    percepts.append('Stench')
                if (nr, nc) in self.pits_pos:
                    percepts.append('Breeze')
        return list(set(percepts)) # Remove duplicates

    def display_grid(self):
        for row in self.grid:
            print(' '.join(row))
        print(f"Caçador em: {self.hunter_pos}")
        print(f"Ouro: {'Sim' if self.has_gold else 'Não'}")
        print(f"Flecha: {'Sim' if self.has_arrow else 'Não'}")
        print(f"Vivo: {'Sim' if self.is_alive else 'Não'}")
        print(f"Pontuação: {self.score}")
        print("---------------------")


if __name__ == '__main__':
    game = WumpusWorld(size=4, num_pits=2, num_wumpus=1)
    game.display_grid()

    # Example game flow
    # game.move_hunter(0, 1) # Move right
    # game.display_grid()
    # game.move_hunter(1, 0) # Move down
    # game.display_grid()
    # game.grab_gold()
    # game.display_grid()
    # game.move_hunter(-1, 0) # Move up
    # game.display_grid()
    # game.move_hunter(0, -1) # Move left
    # game.display_grid()
    # game.climb_out()

    # You can add more interactive input here for testing

