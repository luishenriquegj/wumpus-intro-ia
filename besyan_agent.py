import heapq
import numpy as np

class BayesianAgent:
    def __init__(self, size):
        self.size = size
        self.P_wumpus = np.ones((size, size))
        self.P_wumpus[0, 0] = 0
        self.P_wumpus /= np.sum(self.P_wumpus)

        self.P_pit = np.ones((size, size)) * 0.15
        self.P_pit[0, 0] = 0.0

        self.P_gold = np.ones((size, size))
        self.P_gold[0, 0] = 0
        self.P_gold /= np.sum(self.P_gold)
        self.nodes_expanded = 0

        self.current_path = []
        self.visited = set()
        self.history = [(0,0)]
        self.gold_found = False
        self.breeze_locs = set()

    def predict(self):
        # Cria uma nova matriz para armazenar a probabilidade atualizada
        new_P = np.zeros_like(self.P_wumpus)

        # Percorre todas as células do tabuleiro
        for x in range(self.size):
            for y in range(self.size):
                prob = self.P_wumpus[x, y]

                # Se a probabilidade é zero, ignora a célula
                if prob == 0:
                    continue

                # 50% da probabilidade: o Wumpus permanece na mesma célula
                new_P[x, y] += 0.5 * prob

                # Calcula os vizinhos da célula
                neighbors = []
                if x > 0: neighbors.append((x-1, y))
                if x < self.size-1: neighbors.append((x+1, y))
                if y > 0: neighbors.append((x, y-1))
                if y < self.size-1: neighbors.append((x, y+1))

                # Se existirem vizinhos, o Wumpus distribui 50% para eles
                if neighbors:
                    prob_move = (0.5 * prob) / len(neighbors)

                    # Cada vizinho recebe uma fatia igual dessa probabilidade
                    for nx, ny in neighbors:
                        new_P[nx, ny] += prob_move

                else:
                    # Caso raro: célula isolada (sem vizinhos)
                    # Mantém os outros 50% na própria célula
                    new_P[x, y] += 0.5 * prob

        # Atualiza a matriz de probabilidade do Wumpus
        self.P_wumpus = new_P

    def update(self, percepts, agent_pos):
        self.visited.add(agent_pos)
        ax, ay = agent_pos

        if not self.history or self.history[-1] != agent_pos:
            self.history.append(agent_pos)

        if "Brilho" in percepts:
            likelihood_gold = np.zeros_like(self.P_gold)
            for x in range(self.size):
                for y in range(self.size):
                    dist = abs(x - ax) + abs(y - ay)
                    if dist <= 1:  # ouro gera brilho na vizinhança imediata
                        likelihood_gold[x, y] = 1.0
                    else:
                        likelihood_gold[x, y] = 0.0
            self.P_gold *= likelihood_gold
        else:
            # Se NÃO tem brilho, então ouro não está na vizinhança imediata
            for x in range(self.size):
                for y in range(self.size):
                    dist = abs(x - ax) + abs(y - ay)
                    if dist <= 1:
                        self.P_gold[x, y] = 0.0

        # 1. Wumpus
        self.predict()
        has_stench = "Fedor" in percepts
        ax, ay = agent_pos
        likelihood = np.zeros_like(self.P_wumpus)

        for x in range(self.size):
            for y in range(self.size):
                dist = abs(x - ax) + abs(y - ay)
                if has_stench: likelihood[x, y] = 1.0 if dist <= 2 else 0.0
                else: likelihood[x, y] = 0.0 if dist <= 2 else 1.0

        self.P_wumpus *= likelihood
        total = np.sum(self.P_wumpus)
        if total > 0: self.P_wumpus /= total
        else: self.P_wumpus = np.ones((self.size, self.size))

        # 2. Buracos (Atualização Local)
        self.P_pit[ax, ay] = 0.0
        breeze_count = percepts.count("Brisa")
        has_breeze = breeze_count > 0

        if has_breeze:
            self.breeze_locs.add(agent_pos)
        else:
            if agent_pos in self.breeze_locs: self.breeze_locs.remove(agent_pos)

        neighbors = []
        if ax > 0: neighbors.append((ax-1, ay))
        if ax < self.size-1: neighbors.append((ax+1, ay))
        if ay > 0: neighbors.append((ax, ay-1))
        if ay < self.size-1: neighbors.append((ax, ay+1))

        if not has_breeze:
            for nx, ny in neighbors: self.P_pit[nx, ny] = 0.0
        else:
            # Risco 0.2 (20%) se tiver 1 brisa. Risco 0.9 (90%) se tiver 2+.
            risk_level = 0.9 if breeze_count >= 2 else 0.2
            for nx, ny in neighbors:
                if self.P_pit[nx, ny] != 0.0 and self.P_pit[nx, ny] != 1.0:
                    self.P_pit[nx, ny] = max(self.P_pit[nx, ny], risk_level)

        # 3. Inferência Lógica (Minesweeper)
        changed = True
        while changed:
            changed = False
            for (bx, by) in self.breeze_locs:
                b_neighbors = []
                if bx > 0: b_neighbors.append((bx-1, by))
                if bx < self.size-1: b_neighbors.append((bx+1, by))
                if by > 0: b_neighbors.append((bx, by-1))
                if by < self.size-1: b_neighbors.append((bx, by+1))

                potential_pits = []
                for nx, ny in b_neighbors:
                    if self.P_pit[nx, ny] > 0.0:
                        potential_pits.append((nx, ny))

                if len(potential_pits) == 1:
                    px, py = potential_pits[0]
                    if self.P_pit[px, py] != 1.0:
                        self.P_pit[px, py] = 1.0 # CERTEZA
                        changed = True

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # CALCULA PERIGO E CUSTO
    def get_danger_cost(self, pos):
        risk = self.P_wumpus[pos] + self.P_pit[pos]
        return 1 + (risk * 1000)
    
    #FUNÇÃO 'PLANO DE EMERGENCIA' DO AGENTE
    # - não encontra um alvo razoável na fronteira
    # - não tem mais informação suficiente para decidir para onde ir
    # - não encontra nenhuma célula segura para explorar
    # ESSE MÉTODO:
        # 1 - procura todas as células não visitadas
        # 2 - calcula o risco de cada célula e a distancia da posição atual
        # 3 - Ordena por:
            # - menor risco
            # - menor distância
        # 4 - Retorna a célula mais promissora → a menos perigosa disponível
    def super_safe_fallback(self, current_pos):
        candidates = []
        for x in range(self.size):
            for y in range(self.size):
                pos = (x, y)
                if pos in self.visited: continue
                risk = self.P_wumpus[x, y] + self.P_pit[x, y]
                dist = abs(x - current_pos[0]) + abs(y - current_pos[1])
                candidates.append((risk, dist, pos))
        if not candidates: return None
        candidates.sort()
        return candidates[0][2]


    def find_best_target(self, current_pos):
        frontier = []
        for x in range(self.size):
            for y in range(self.size):
                pos = (x, y)
                if pos in self.visited: 
                    continue
                # verifica se está na fronteira (adjacente a uma célula visitada)
                is_frontier = False
                px, py = pos
                neighbors = []
                if px > 0: neighbors.append((px-1, py))
                if px < self.size-1: neighbors.append((px+1, py))
                if py > 0: neighbors.append((px, py-1))
                if py < self.size-1: neighbors.append((px, py+1))

                for n in neighbors:
                    if n in self.visited:
                        is_frontier = True
                        break

                if not is_frontier:
                    # o agente não vê ainda — empurra para baixo na prioridade
                    continue

                # risco + distância para ordenação
                risk = self.P_wumpus[x, y] + self.P_pit[x, y]
                dist = abs(x - current_pos[0]) + abs(y - current_pos[1])

                frontier.append((risk, dist, pos))
            self.nodes_expanded += 1
        # se existem células na fronteira, usa elas
        if frontier:
            frontier.sort()
            return frontier[0][2]

        # fallback: caso a fronteira acabe, usar o método pra cenários extremos
        return super_safe_fallback(self, current_pos)

    
    def a_star(self, start, goal, tolerance=0.5):
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal: break
            x, y = current
            neighbors = []
            if x > 0: neighbors.append((x-1, y))
            if x < self.size-1: neighbors.append((x+1, y))
            if y > 0: neighbors.append((x, y-1))
            if y < self.size-1: neighbors.append((x, y+1))

            for next_pos in neighbors:
                risk = self.P_wumpus[next_pos] + self.P_pit[next_pos]
                if risk > tolerance: continue
                new_cost = cost_so_far[current] + 1 + (risk * 100)
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        if goal not in came_from: return []
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        self.current_path = path
        return path

    def choose_action(self, agent_pos, actual_gold_pos):
        # 1. Se o agente achou o ouro (detectou brilho)
        if self.gold_found:
            target = actual_gold_pos
        else:
            target = self.find_best_target(agent_pos)

        if target is None:
            return None

        # Caminho seguro
        path = self.a_star(agent_pos, target, tolerance=0.0)

        # Caso extremo: tenta com tolerância maior
        if not path:
            path = self.a_star(agent_pos, target, tolerance=0.3)

        if not path:
            return None

        next_step = path[0]
        dx = next_step[0] - agent_pos[0]
        dy = next_step[1] - agent_pos[1]

        if dx == -1: return 'N'
        if dx == 1: return 'S'
        if dy == 1: return 'L'
        if dy == -1: return 'O'
        return None