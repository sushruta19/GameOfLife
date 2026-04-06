"""
engine.py
Simulation Engine for Conway's Game of Life (Toroidal)
"""
from typing import Set, Tuple, Dict, Iterable, Optional

class Universe:
    _NEIGHBOURS = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1)
    )

    def __init__(self, width: int = 50, height: int = 50, initial_state: Optional[Iterable[Tuple[int, int]]] = None) -> None:
        self.width = width
        self.height = height
        self.live_cells: Set[Tuple[int, int]] = set()
        self.generation = 0
        if initial_state:
            for x, y in initial_state:
                self.add_cell(x, y)

    def add_cell(self, x: int, y: int) -> None:
        self.live_cells.add((x % self.width, y % self.height))
    
    def remove_cell(self, x: int, y: int) -> None:
        self.live_cells.discard((x % self.width, y % self.height))
    
    def toggle_cell(self, x: int, y: int) -> None:
        cell = (x % self.width, y % self.height)
        if cell in self.live_cells:
            self.live_cells.remove(cell)
        else:
            self.live_cells.add(cell)
    
    def is_alive(self, x: int, y: int) -> bool:
        return (x % self.width, y % self.height) in self.live_cells
    
    def count_neighbours(self) -> Dict[Tuple[int, int], int]:
        neighbour_counts: Dict[Tuple[int, int], int] = {}
        for (x, y) in self.live_cells:
            for dx, dy in self._NEIGHBOURS:
                # Wrap neighbour coordinates around the edges
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbour = (nx, ny)
                neighbour_counts[neighbour] = neighbour_counts.get(neighbour, 0) + 1
        
        return neighbour_counts

    def step(self):
        neighbour_counts: Dict[Tuple[int, int], int] = self.count_neighbours()
        new_live_cells: Set[Tuple[int, int]] = set()

        for cell, count in neighbour_counts.items():
            if cell in self.live_cells:
                if count == 2 or count == 3:
                    new_live_cells.add(cell)
            else:
                if count == 3:
                    new_live_cells.add(cell)
        
        self.live_cells = new_live_cells
        self.generation += 1

    def population(self) -> int:
        return len(self.live_cells)
    
    def clear(self) -> None:
        self.live_cells.clear()
        self.generation = 0
    
    def load_pattern(self, pattern: Iterable[Tuple[int, int]], offset_x: int = 0, offset_y: int = 0) -> None:
        for x, y in pattern:
            self.add_cell(x + offset_x, y + offset_y)