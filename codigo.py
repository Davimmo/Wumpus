# -*- coding: utf-8 -*-
"""
Mundo do Wumpus com Agente de Lógica Proposicional (Solucionável com Ouro)

Este script implementa o jogo Mundo do Wumpus usando Pygame.
O agente (caçador) utiliza uma base de conhecimento e regras de
lógica proposicional para inferir quais células do mapa são seguras,
perigosas ou desconhecidas.

Novas funcionalidades:
- Ouro (G) foi adicionado ao mapa como objetivo.
- O agente percebe um "Brilho" na casa do ouro.
- O objetivo é pegar o ouro e voltar à casa inicial para vencer.
- O problema é sempre solucionável: Wumpus, buracos e ouro não podem
  aparecer na casa inicial ou em suas adjacentes.
- O mapa sempre contém 1 Wumpus, 2 Buracos e 1 Ouro.
"""

import pygame
import sys
import random
import collections # Adicionado para deque

# --- Configurações do Jogo ---
TILE_SIZE = 120
GRID_SIZE = 4
WIDTH, HEIGHT = TILE_SIZE * GRID_SIZE, TILE_SIZE * GRID_SIZE + 100
FPS = 30

# --- Cores ---
GRAY = (180, 180, 180)    # Célula Desconhecida
GREEN = (0, 200, 0)      # Célula Segura
RED = (200, 0, 0)        # Célula Perigosa
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)  # Célula Já Visitada
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)     # Cor do Ouro
BLUE = (0, 0, 200)

# --- Inicialização do Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mundo do Wumpus - Lógica Proposicional")
font = pygame.font.SysFont("Arial", 24)
status_font = pygame.font.SysFont("Arial", 28, bold=True)
icon_font = pygame.font.SysFont("Arial", 48)
danger_font = pygame.font.SysFont("Arial", 80, bold=True)

# --- Classe Principal do Mundo ---
class WumpusWorld:
    def __init__(self):
        self.GRID_SIZE = GRID_SIZE # Adiciona GRID_SIZE como atributo da instância
        self.reset()

    def get_adjacent(self, x, y):
        """Retorna uma lista de células adjacentes válidas."""
        adj = []
        if x > 0: adj.append((x - 1, y))
        if x < self.GRID_SIZE - 1: adj.append((x + 1, y))
        if y > 0: adj.append((x, y - 1))
        if y < self.GRID_SIZE - 1: adj.append((x, y + 1))
        return adj

    def reset(self):
        """Inicializa ou reinicia o estado do mundo e do agente."""
        self.start_pos = (0, self.GRID_SIZE - 1)
        self.agent_pos = self.start_pos
        self.has_gold = False
        self.game_over = False
        self.victory = False

        # Usar a nova função para gerar um mapa solucionável
        self.wumpus, self.holes, self.gold = self._generate_solvable_map(self.GRID_SIZE, self.start_pos)

        self._world_percepts = self._generate_all_percepts()

        # --- Conhecimento do agente ---
        self.visited = set()
        self.safe = {self.start_pos}
        self.danger = set()
        self.unknown = set([(x, y) for x in range(self.GRID_SIZE) for y in range(self.GRID_SIZE)])
        self.unknown.remove(self.start_pos)
        self.knowledge_base = {}
        self.history = []

    def _is_path_valid(self, start, end, obstacles, grid_size):
        """Verifica se existe um caminho válido entre start e end, evitando obstáculos."""
        queue = collections.deque([(start, [start])])  # (posição atual, caminho percorrido)
        visited = {start}

        while queue:
            (r, c), path = queue.popleft()

            if (r, c) == end:
                return True, path

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc

                if 0 <= nr < grid_size and 0 <= nc < grid_size and \
                   (nr, nc) not in obstacles and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), path + [((nr, nc))]))
        return False, []

    def _generate_solvable_map(self, grid_size, start_pos, num_holes=2):
        """Gera um mapa do Wumpus que é garantidamente solucionável."""
        all_cells = [(x, y) for x in range(grid_size) for y in range(grid_size)]
        forbidden_initial_cells = {start_pos} | set(self.get_adjacent(start_pos[0], start_pos[1]))

        while True:
            # 1. Posicionar Wumpus
            possible_wumpus_cells = [c for c in all_cells if c not in forbidden_initial_cells]
            wumpus_pos = random.choice(possible_wumpus_cells)

            # 2. Posicionar Ouro
            possible_gold_cells = [c for c in all_cells if c not in forbidden_initial_cells and c != wumpus_pos]
            gold_pos = random.choice(possible_gold_cells)

            # 3. Posicionar Buracos
            possible_hole_cells = [c for c in all_cells if c not in forbidden_initial_cells and c != wumpus_pos and c != gold_pos]
            if len(possible_hole_cells) < num_holes:
                continue # Não há células suficientes para os buracos
            holes_pos = random.sample(possible_hole_cells, num_holes)

            # Verificar solvabilidade
            obstacles_to_gold = {wumpus_pos} | set(holes_pos)
            path_to_gold_exists, path_to_gold = self._is_path_valid(start_pos, gold_pos, obstacles_to_gold, grid_size)

            if path_to_gold_exists:
                # Agora, verificar se é possível voltar do ouro para o início
                path_back_exists, _ = self._is_path_valid(gold_pos, start_pos, obstacles_to_gold, grid_size)
                if path_back_exists:
                    return wumpus_pos, holes_pos, gold_pos

    def _generate_all_percepts(self):
        """Cria o mapa de percepções (informação do ambiente)."""
        percepts = {}
        for x in range(self.GRID_SIZE):
            for y in range(self.GRID_SIZE):
                fedor = any(neighbor == self.wumpus for neighbor in self.get_adjacent(x, y))
                vento = any(neighbor in self.holes for neighbor in self.get_adjacent(x, y))
                brilho = (x, y) == self.gold
                percepts[(x, y)] = (fedor, vento, brilho)
        return percepts

    def sense_at_current_pos(self):
        """O agente sente o ambiente na sua posição atual."""
        return self._world_percepts[self.agent_pos]

    def _get_percept_counts(self, cell_type):
        """Conta quantas células adjacentes a uma célula desconhecida possuem a percepção de fedor ou vento."""
        counts = collections.defaultdict(int)

        for pos, (fedor, vento, brilho) in self.knowledge_base.items():
            if (cell_type == 'wumpus' and fedor) or (cell_type == 'hole' and vento):
                for neighbor in self.get_adjacent(pos[0], pos[1]):
                    if neighbor in self.unknown:
                        counts[neighbor] += 1
        return counts

    def logical_update(self):
        """Atualiza a base de conhecimento e realiza inferências lógicas."""
        pos = self.agent_pos
        if pos in self.visited:
            return

        self.visited.add(pos)
        self.unknown.discard(pos)
        self.safe.add(pos)
        
        fedor, vento, brilho = self.sense_at_current_pos()
        self.knowledge_base[pos] = (fedor, vento, brilho)

        if brilho:
            self.has_gold = True
            print("OURO ENCONTRADO E COLETADO!")

        # Regra 1: Se não há percepções, todos os vizinhos são seguros.
        if not fedor and not vento:
            for neighbor in self.get_adjacent(pos[0], pos[1]):
                if neighbor not in self.visited:
                    self.safe.add(neighbor)
                    self.unknown.discard(neighbor)

        # Regra 2: Inferir perigo por eliminação (Poço ou Wumpus).
        # Se uma célula tem vento/fedor e todos os seus vizinhos, exceto um, são seguros,
        # então o vizinho restante deve ser um buraco/wumpus.
        for cell, (f, v, b) in list(self.knowledge_base.items()): # Usar list() para evitar RuntimeError: dictionary changed size during iteration
            adjacents = self.get_adjacent(cell[0], cell[1])
            unknown_neighbors = [n for n in adjacents if n in self.unknown]
            safe_neighbors = [n for n in adjacents if n in self.safe]

            if v: # Vento -> Poço
                # Se todos os vizinhos, exceto um, são seguros, o restante é um buraco
                if len(adjacents) - len(safe_neighbors) == 1:
                    for un in unknown_neighbors:
                        if un not in self.danger: # Evita adicionar duplicatas ou remover algo já inferido
                            self.danger.add(un)
                            self.unknown.discard(un)
                            print(f"Inferido perigo (Buraco) em {un} devido a vento em {cell}")
            if f: # Fedor -> Wumpus
                # Se todos os vizinhos, exceto um, são seguros, o restante é o wumpus
                if len(adjacents) - len(safe_neighbors) == 1:
                    for un in unknown_neighbors:
                        if un not in self.danger: # Evita adicionar duplicatas ou remover algo já inferido
                            self.danger.add(un)
                            self.unknown.discard(un)
                            print(f"Inferido perigo (Wumpus) em {un} devido a fedor em {cell}")

        # Regra 2.5: Inferir perigo por múltiplas percepções
        wumpus_counts = self._get_percept_counts("wumpus")
        for cell, count in wumpus_counts.items():
            if count > 1 and cell not in self.danger:
                self.danger.add(cell)
                self.unknown.discard(cell)
                print(f"Inferido perigo (Wumpus) em {cell} por múltiplas percepções de fedor.")

        hole_counts = self._get_percept_counts("hole")
        for cell, count in hole_counts.items():
            if count > 1 and cell not in self.danger:
                self.danger.add(cell)
                self.unknown.discard(cell)
                print(f"Inferido perigo (Buraco) em {cell} por múltiplas percepções de vento.")

        # Regra 3: Inferir segurança por eliminação.
        # Se uma célula com perigo (vento/fedor) tem todos os seus vizinhos conhecidos como seguros,
        # então o perigo não pode estar ali. (Isso é mais para refinar, mas a regra 2 já lida com isso indiretamente)
        # No entanto, podemos inferir que se uma célula *não* tem vento/fedor, seus vizinhos são seguros.
        # Isso já é coberto pela Regra 1. A otimização aqui seria mais complexa, envolvendo a contagem de perigos.
        # Por enquanto, a Regra 2 aprimorada é um bom passo.

        # --- NOVA REGRA: Inferir posição exata do Wumpus por múltiplos fedores ---
        # Se uma célula desconhecida é adjacente a duas ou mais células que têm fedor,
        # o agente pode inferir que o Wumpus está nessa célula.
        
        inferred_wumpus = None
        wumpus_candidates = collections.defaultdict(int)

        for pos, (fedor, vento, brilho) in self.knowledge_base.items():
            if fedor:
                for neighbor in self.get_adjacent(pos[0], pos[1]):
                    if neighbor in self.unknown:
                        wumpus_candidates[neighbor] += 1

        # Procura célula com múltiplas evidências de fedor
        for cell, count in wumpus_candidates.items():
            if count > 1:  # duas ou mais células com fedor apontam pra ela
                inferred_wumpus = cell
                break

        # Se o Wumpus foi inferido logicamente
        if inferred_wumpus and inferred_wumpus not in self.danger:
            self.danger.add(inferred_wumpus)
            self.unknown.discard(inferred_wumpus)
            print(f"Inferido Wumpus em {inferred_wumpus} por múltiplas percepções adjacentes de fedor.")

            # Marca as células adjacentes ao Wumpus inferido como seguras, exceto buracos
            for neighbor in self.get_adjacent(inferred_wumpus[0], inferred_wumpus[1]):
                if neighbor not in self.holes and neighbor not in self.danger:
                    self.safe.add(neighbor)
                    self.unknown.discard(neighbor)
                    print(f"Inferido segurança em {neighbor} (adjacente ao Wumpus inferido).")


        # Regra 4: Se a localização do Wumpus é conhecida, as células adjacentes às que têm fedor são seguras (exceto buracos).
        # Raciocínio:
        # Se o agente já sabe onde está o Wumpus, qualquer célula que tem fedor
        # só o tem por estar adjacente ao Wumpus. Assim, as demais adjacentes dessa
        # célula não podem conter o Wumpus — logo, são seguras a menos que sejam buracos.

        if self.wumpus in self.danger:  # Se o Wumpus foi inferido
            wumpus_pos = self.wumpus
        else:
            # Caso o agente tenha inferido logicamente um Wumpus (sem saber da posição real)
            inferred_wumpus_list = [c for c in self.danger if c != self.wumpus]
            wumpus_pos = inferred_wumpus_list[0] if inferred_wumpus_list else None

        if wumpus_pos:
            for cell, (fedor, vento, brilho) in self.knowledge_base.items():
                if fedor:
                    for neighbor in self.get_adjacent(cell[0], cell[1]):
                        if neighbor not in self.holes and neighbor not in self.danger:
                            self.safe.add(neighbor)
                            self.unknown.discard(neighbor)
                            print(f"Inferido segurança em {neighbor} (adjacente a célula com fedor e Wumpus conhecido).")

        # --- Verificação de Game Over mais robusta ---
        # Se não há mais células seguras e não visitadas, e o agente não tem o ouro e não está na posição inicial,
        # e não há caminho para nenhuma célula segura e não visitada, então é Game Over.
        safe_unvisited = {c for c in self.safe if c not in self.visited and c not in self.danger}
        if not self.has_gold and not self.victory and not safe_unvisited and self.agent_pos != self.start_pos:
            # Verifica se há algum caminho para alguma célula segura e não visitada a partir de qualquer célula segura
            can_reach_any_safe_unvisited = False
            for s_cell in self.safe:
                if self._find_path_to_target(s_cell, None, self.safe - self.danger, target_is_set=True, target_set=safe_unvisited):
                    can_reach_any_safe_unvisited = True
                    break

            if not can_reach_any_safe_unvisited:
                self.game_over = True
                print("GAME OVER: Agente preso ou sem movimentos seguros para explorar novas células.")

        
                    
    def step(self):
        """Executa uma jogada do agente."""
        if self.game_over or self.victory:
            return
            
        self.logical_update()
        
        safe_unvisited = {c for c in self.safe if c not in self.visited and c not in self.danger}
        safe_visited = {c for c in self.safe if c in self.visited and c not in self.danger}

        next_pos = None

        # 1. Se tem o ouro, o objetivo é voltar para o início
        if self.has_gold:
            path_to_start = self._find_path_to_target(self.agent_pos, self.start_pos, self.safe - self.danger)
            if path_to_start and len(path_to_start) > 1:
                next_pos = path_to_start[1]
            else:
                # Se não encontrou um caminho para o início (o que não deveria acontecer em um mapa solucionável)
                # Tenta mover para uma célula segura adjacente já visitada para não ficar preso
                adj_safe_visited = [c for c in self.get_adjacent(self.agent_pos[0], self.agent_pos[1]) if c in safe_visited]
                if adj_safe_visited:
                    next_pos = random.choice(adj_safe_visited)

        # 2. Se não tem o ouro, explora
        if not self.has_gold and next_pos is None:
            # Prioriza células seguras e não visitadas adjacentes
            adj_safe_unvisited = [c for c in self.get_adjacent(self.agent_pos[0], self.agent_pos[1]) if c in safe_unvisited]
            if adj_safe_unvisited:
                next_pos = random.choice(adj_safe_unvisited)
            else:
                # Se não há células seguras e não visitadas adjacentes, tenta encontrar um caminho para a célula segura não visitada mais próxima
                # Isso evita que o agente fique preso em um loop de células visitadas
                if safe_unvisited:
                    path_to_closest_safe_unvisited = self._find_path_to_target(self.agent_pos, None, self.safe - self.danger, target_is_set=True, target_set=safe_unvisited)
                    if path_to_closest_safe_unvisited and len(path_to_closest_safe_unvisited) > 1:
                        next_pos = path_to_closest_safe_unvisited[1]
                    else:
                        # Se não encontrou um caminho para uma célula segura não visitada, tenta mover para uma célula segura adjacente já visitada
                        adj_safe_visited = [c for c in self.get_adjacent(self.agent_pos[0], self.agent_pos[1]) if c in safe_visited]
                        if adj_safe_visited:
                            next_pos = random.choice(adj_safe_visited)
                else:
                    # Se todas as células seguras foram visitadas, o agente pode estar preso ou o mapa é muito restritivo
                    # Tenta mover para uma célula segura adjacente já visitada para não ficar parado
                    adj_safe_visited = [c for c in self.get_adjacent(self.agent_pos[0], self.agent_pos[1]) if c in safe_visited]
                    if adj_safe_visited:
                        next_pos = random.choice(adj_safe_visited)
                    else:
                        # Se não há mais células seguras para explorar e o ouro não foi encontrado,
                        # o agente pode estar preso ou não há mais movimentos possíveis.
                        # Neste caso, o jogo deve terminar, mas não como uma derrota se ainda houver células desconhecidas.
                        # A condição de game over será ajustada na próxima fase.
                        pass

        # --- GARANTIA: O agente nunca entra na célula do Wumpus ---
        if next_pos == self.wumpus:
            print(f"Evitei mover para {next_pos} (Wumpus conhecido). Procurando alternativa segura.")
            # remove essa célula do conjunto seguro para evitar futuros erros
            self.safe.discard(next_pos)
            self.danger.add(next_pos)
            self.unknown.discard(next_pos)
            next_pos = None

        # Se ainda há movimento possível
        if next_pos:
            self.history.append(self.agent_pos)
            self.agent_pos = next_pos

            # Verifica as condições de vitória/derrota após o movimento
            if self.agent_pos in self.holes:
                print("GAME OVER! Agente caiu em um buraco.")
                self.game_over = True
            elif self.agent_pos == self.wumpus:
                print("GAME OVER! O agente foi morto pelo Wumpus.")
                self.game_over = True
            elif self.has_gold and self.agent_pos == self.start_pos:
                print("VITÓRIA! O agente escapou com o ouro.")
                self.victory = True


    def back(self):
        """Volta para a posição anterior."""
        if self.history and not self.game_over and not self.victory:
            self.agent_pos = self.history.pop()

    def _find_path_to_target(self, start, target, safe_cells, target_is_set=False, target_set=None):
        """Encontra um caminho seguro do início ao alvo (ou ao conjunto de alvos) usando BFS."""
        queue = collections.deque([(start, [start])])
        local_visited = {start}

        while queue:
            current_pos, path = queue.popleft()

            if target_is_set:
                if current_pos in target_set:
                    return path
            elif current_pos == target:
                return path

            for neighbor in self.get_adjacent(current_pos[0], current_pos[1]):
                if neighbor in safe_cells and neighbor not in local_visited:
                    local_visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None # Nenhum caminho encontrado

# --- Funções de Desenho ---
def draw_world(world):
    """Desenha o estado atual do mundo."""
    screen.fill(BROWN)
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            cell = (x, y)
            color = GRAY # Padrão: Desconhecido

            if cell in world.visited: color = WHITE
            elif cell in world.safe: color = GREEN
            elif cell in world.danger: color = RED
            
            pygame.draw.rect(screen, color, rect)

            # MOSTRA A LOCALIZAÇÃO REAL DOS ITENS (APENAS PARA O USUÁRIO)
            if cell == world.gold:
                g_text = danger_font.render("G", True, GOLD)
                text_rect = g_text.get_rect(center=rect.center)
                screen.blit(g_text, text_rect)
            
            if cell == world.wumpus:
                w_text = danger_font.render("W", True, (150, 0, 0))
                text_rect = w_text.get_rect(center=rect.center)
                screen.blit(w_text, text_rect)
            elif cell in world.holes:
                b_text = danger_font.render("B", True, BLACK)
                text_rect = b_text.get_rect(center=rect.center)
                screen.blit(b_text, text_rect)

            pygame.draw.rect(screen, BLACK, rect, 2)

            # Desenha as percepções das células visitadas
            if cell in world.knowledge_base:
                fedor, vento, brilho = world.knowledge_base[cell]
                if fedor: screen.blit(icon_font.render("F", True, BLACK), (rect.left + 5, rect.top))
                if vento: screen.blit(icon_font.render("V", True, BLUE), (rect.right - 35, rect.top))
                if brilho: pygame.draw.polygon(screen, GOLD, [(rect.centerx, rect.top + 5), (rect.right-5, rect.centery), (rect.centerx, rect.bottom-5), (rect.left+5, rect.centery)])

    # Desenha o agente
    ax, ay = world.agent_pos
    agent_center = (ax * TILE_SIZE + TILE_SIZE // 2, ay * TILE_SIZE + TILE_SIZE // 2)
    pygame.draw.circle(screen, BLUE, agent_center, TILE_SIZE // 3)
    
    draw_ui(world)

def draw_ui(world):
    """Desenha a interface de botões e status."""
    ui_area = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    pygame.draw.rect(screen, BLACK, ui_area)
    
    # Botões
    back_btn = pygame.Rect(10, HEIGHT - 85, 160, 50)
    next_btn = pygame.Rect(WIDTH - 170, HEIGHT - 85, 160, 50)
    reset_btn = pygame.Rect(WIDTH // 2 - 80, HEIGHT - 90, 160, 60)

    pygame.draw.rect(screen, GRAY, back_btn, border_radius=10)
    pygame.draw.rect(screen, GRAY, next_btn, border_radius=10)
    pygame.draw.rect(screen, (200, 50, 50), reset_btn, border_radius=10)

    screen.blit(font.render("← Voltar", True, BLACK), (back_btn.centerx - 40, back_btn.centery - 12))
    screen.blit(font.render("Próximo →", True, BLACK), (next_btn.centerx - 45, next_btn.centery - 12))
    screen.blit(font.render("Reiniciar", True, WHITE), (reset_btn.centerx - 45, reset_btn.centery - 12))
    
    # Texto de status
    status_text = "Caçando o ouro..."
    status_color = WHITE
    if world.has_gold:
        status_text = "Ouro encontrado! Volte para (0,3)"
    if world.victory:
        status_text = "VOCÊ VENCEU!"
        status_color = GREEN
    elif world.game_over:
        status_text = "GAME OVER!"
        status_color = RED

    status_surf = status_font.render(status_text, True, status_color)
    screen.blit(status_surf, (ui_area.centerx - status_surf.get_width()//2, ui_area.top + 5))
    

def main():
    world = WumpusWorld()
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Botão de Voltar
                if 10 <= event.pos[0] <= 170 and HEIGHT - 85 <= event.pos[1] <= HEIGHT - 35:
                    world.back()
                # Botão de Próximo
                elif WIDTH - 170 <= event.pos[0] <= WIDTH - 10 and HEIGHT - 85 <= event.pos[1] <= HEIGHT - 35:
                    world.step()
                # Botão de Reiniciar
                elif WIDTH // 2 - 80 <= event.pos[0] <= WIDTH // 2 + 80 and HEIGHT - 90 <= event.pos[1] <= HEIGHT - 30:
                    world.reset()

        draw_world(world)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()