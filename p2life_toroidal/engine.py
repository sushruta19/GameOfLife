"""
engine.py (p2life_toroidal variant)
Simulation Engine for Two-Player Conway's Game of Life on a 3D Torus
"""
import random
from typing import Tuple, Dict, Iterable, Optional

WHITE = 1
BLACK = 2

class Universe:
    _NEIGHBOURS = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),  (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    )

    def __init__(self, width: int = 50, height: int = 50, initial_state: Optional[Dict[Tuple[int, int], int]] = None) -> None:
        self.width = width
        self.height = height
        self.live_cells: Dict[Tuple[int, int], int] = initial_state.copy() if initial_state else {}
        self.generation = 0

    def add_cell(self, x: int, y: int, player: int = WHITE) -> None:
        self.live_cells[(x % self.width, y % self.height)] = player
    
    def remove_cell(self, x: int, y: int) -> None:
        self.live_cells.pop((x % self.width, y % self.height), None)
    
    def toggle_cell(self, x: int, y: int, player: int = WHITE) -> None:
        cell = (x % self.width, y % self.height)
        if cell in self.live_cells:
            del self.live_cells[cell]
        else:
            self.live_cells[cell] = player
    
    def is_alive(self, x: int, y: int) -> bool:
        return (x % self.width, y % self.height) in self.live_cells
    
    def get_cell_owner(self, x: int, y: int) -> Optional[int]:
        return self.live_cells.get((x % self.width, y % self.height))

    def count_neighbours(self) -> Dict[Tuple[int, int], Dict[int, int]]:
        neighbour_counts: Dict[Tuple[int, int], Dict[int, int]] = {}
        
        for (x, y), owner in self.live_cells.items():
            for dx, dy in self._NEIGHBOURS:
                # Wrap neighbour coordinates around the edges of the Torus
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbour = (nx, ny)
                
                if neighbour not in neighbour_counts:
                    neighbour_counts[neighbour] = {WHITE: 0, BLACK: 0}
                
                neighbour_counts[neighbour][owner] += 1
        
        return neighbour_counts

    def step(self):
        neighbour_counts = self.count_neighbours()
        new_live_cells: Dict[Tuple[int, int], int] = {}

        for cell, counts in neighbour_counts.items():
            w = counts[WHITE]
            b = counts[BLACK]
            
            if cell in self.live_cells:
                owner = self.live_cells[cell]
                
                if owner == WHITE:
                    diff = w - b
                    if diff == 2 or diff == 3:
                        new_live_cells[cell] = WHITE
                    elif diff == 1 and w >= 2:
                        new_live_cells[cell] = WHITE
                
                elif owner == BLACK:
                    diff = b - w
                    if diff == 2 or diff == 3:
                        new_live_cells[cell] = BLACK
                    elif diff == 1 and b >= 2:
                        new_live_cells[cell] = BLACK

            else:
                if w == 3 and b != 3:
                    new_live_cells[cell] = WHITE
                elif b == 3 and w != 3:
                    new_live_cells[cell] = BLACK
                elif w == 3 and b == 3:
                    winner = random.choice([WHITE, BLACK])
                    new_live_cells[cell] = winner
        
        self.live_cells = new_live_cells
        self.generation += 1

    def population(self) -> Tuple[int, int]:
        white_count = sum(1 for owner in self.live_cells.values() if owner == WHITE)
        black_count = len(self.live_cells) - white_count
        return white_count, black_count
    
    def clear(self) -> None:
        self.live_cells.clear()
        self.generation = 0
    
    def load_pattern(self, pattern: Iterable[Tuple[int, int]], player: int, offset_x:int = 0, offset_y:int = 0) -> None:
        """Loads a standard pattern array and assigns it to a specific player."""
        for x, y in pattern:
            self.add_cell(x + offset_x, y + offset_y, player)