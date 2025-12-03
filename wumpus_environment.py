import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import random
import time
from IPython.display import clear_output
import heapq
import streamlit as st


# --- CONSTANTES ---
VAZIO = 0
AGENTE = 1
WUMPUS = 2
OURO = 3
BURACO = 4

# --- PARTE 1: O AMBIENTE (FÍSICA) ---
class WumpusEnvironment:
    def __init__(self, size=10, n_pits=15):
        self.size = size
        self.score = 0
        self.n_pits = n_pits
        self.reset()

    def update_score(self, score):
        self.score = score

    def reset(self):
        self.grid = np.zeros((self.size, self.size))
        self.game_over = False
        self.won = False
        self.message = ""
        self.step_count = 0

        coords = [(x, y) for x in range(self.size) for y in range(self.size)]

        self.agent_pos = (0, 0)
        if self.agent_pos in coords: coords.remove(self.agent_pos)

        # Aleatoriedade
        n_items = 2 + self.n_pits
        indices = np.random.choice(len(coords), n_items, replace=False)
        chosen_coords = [coords[i] for i in indices]

        self.wumpus_pos = chosen_coords[0]
        self.gold_pos = chosen_coords[1]
        self.pits_pos = chosen_coords[2:]

        # Gera o chão (textura estática)
        self.floor_map = [[get_sprite('floor') for _ in range(self.size)] for _ in range(self.size)]

        return self.get_observation()

    def get_observation(self):
        percepts = []
        ax, ay = self.agent_pos

         # Brilho: agora o agente percebe quando está no ouro ou adjacente
        gx, gy = self.gold_pos
        if abs(ax - gx) + abs(ay - gy) <= 1:    #  adiciona "brilho" nas casas adjacentes ao ouro
            percepts.append("Brilho")
        

        for px, py in self.pits_pos:
            if abs(ax - px) + abs(ay - py) == 1:
                percepts.append("Brisa")

        wx, wy = self.wumpus_pos
        if abs(ax - wx) + abs(ay - wy) <= 2: percepts.append("Fedor")

        return percepts

    def is_valid_pos(self, pos):
        x, y = pos
        return 0 <= x < self.size and 0 <= y < self.size

    def move_wumpus(self):
        if random.random() < 0.5: return

        wx, wy = self.wumpus_pos
        moves = [(0,1), (0,-1), (1,0), (-1,0)]
        valid_moves = []

        for dx, dy in moves:
            new_pos = (wx + dx, wy + dy)
            is_pit = any(p == new_pos for p in self.pits_pos)
            if self.is_valid_pos(new_pos) and not is_pit:
                valid_moves.append(new_pos)

        if valid_moves:
            self.wumpus_pos = random.choice(valid_moves)

    def step(self, action):
        if self.game_over:
            return self.get_observation(), True, self.score

        self.score -= 1
        self.step_count += 1

        dx, dy = 0, 0
        if action == 'N': dx = -1
        elif action == 'S': dx = 1
        elif action == 'L': dy = 1
        elif action == 'O': dy = -1

        new_pos = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
        if self.is_valid_pos(new_pos):
            self.agent_pos = new_pos
        else:
            self.message = "Parede!"

        if any(p == self.agent_pos for p in self.pits_pos):
            self.game_over = True
            self.message = "MORREU (Buraco)!"
            return self.get_observation(), True, self.score

        self.move_wumpus()

        if self.agent_pos == self.wumpus_pos:
            self.score -= 50
            self.game_over = True
            self.message = "MORREU (Wumpus)!"
            return self.get_observation(), True, self.score

        # vitória → pontuação positiva
        if self.agent_pos == self.gold_pos:
            self.score += 500
            self.game_over = True
            self.won = True
            self.message = "VITORIA!"
            return self.get_observation(), True, self.score

        return self.get_observation(), False, self.score
    
def get_sprite(name):
    # Paletas de Cores (R, G, B)
    palette = {
        'hero':   [[0,0,0], [0,0,0], [30,144,255], [255,215,0]],   # Azul e Dourado
        'wumpus': [[0,0,0], [0,0,0], [220,20,60],  [255,255,255]], # Vermelho e Branco
        'gold':   [[0,0,0], [0,0,0], [255,215,0],  [255,255,224]], # Dourado Brilhante
        'pit':    [[0,0,0], [0,0,0], [20,20,20],   [50,50,50]],    # Cinza Escuro
        # PALETA DE GRAMA:
        'floor':  [[34, 139, 34], [0, 100, 0], [50, 205, 50], [107, 142, 35]] # Verde Floresta, Escuro, Lima
    }

    # Layouts dos Sprites (8x8)
    sprites_idx = {
        'hero': np.array([
            [0,0,1,1,1,1,0,0],
            [0,1,2,2,2,2,1,0],
            [0,1,2,3,3,2,1,0],
            [0,1,2,3,3,2,1,0],
            [0,0,1,2,2,1,0,0],
            [0,1,2,2,2,2,1,0],
            [1,2,1,2,2,1,2,1],
            [1,1,0,1,1,0,1,1]
        ]),
        'wumpus': np.array([
            [0,1,0,0,0,0,1,0],
            [1,2,1,0,0,1,2,1],
            [1,2,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,1],
            [1,2,3,2,2,3,2,1],
            [1,2,2,2,2,2,2,1],
            [0,1,2,1,1,2,1,0],
            [0,1,1,0,0,1,1,0]
        ]),
        'gold': np.array([
            [0,0,0,1,1,0,0,0],
            [0,0,1,2,2,1,0,0],
            [0,1,2,3,3,2,1,0],
            [1,2,3,2,2,3,2,1],
            [1,2,2,2,2,2,2,1],
            [0,1,2,2,2,2,1,0],
            [0,0,1,2,2,1,0,0],
            [0,0,0,1,1,0,0,0]
        ]),
        'pit': np.array([
            [0,0,1,1,1,1,0,0],
            [0,1,2,2,2,2,1,0],
            [1,2,2,2,2,2,2,1],
            [1,2,2,3,3,2,2,1],
            [1,2,2,3,3,2,2,1],
            [1,2,2,2,2,2,2,1],
            [0,1,2,2,2,2,1,0],
            [0,0,1,1,1,1,0,0]
        ])
    }

    # Gera o sprite RGB
    if name == 'floor':
        # Chão é gerado com ruído para parecer grama
        base = np.random.choice([0,1,2], (8,8), p=[0.7, 0.2, 0.1])
        rgb = np.zeros((8,8,3), dtype=int)
        for i in range(8):
            for j in range(8):
                rgb[i,j] = palette['floor'][base[i,j]]
        return rgb

    idx_map = sprites_idx.get(name)
    colors_list = palette.get(name)

    # Cria imagem RGBA (com canal alpha para transparência)
    rgba = np.zeros((8,8,4), dtype=float)

    for i in range(8):
        for j in range(8):
            idx = idx_map[i,j]
            if idx > 0: # Se não for transparente
                col = colors_list[idx]
                rgba[i,j] = [col[0]/255, col[1]/255, col[2]/255, 1.0] # Opaco
            else:
                rgba[i,j] = [0,0,0,0] # Transparente
    return rgba

