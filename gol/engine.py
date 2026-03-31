"""
engine.py
Simulation Engine for Conway's Game of Life
"""
from typing import Set, Tuple, Dict, Iterable, Optional

class Universe:
    """
    Represents infinite Grid by storing the live cells in a Set
    Attributes
    live_cells : Set[Tuple[int, int]]
        Set of coordinates representing current alive cells
    generation : int
        Current generation count
    """
    # Neighbour coords
    _NEIGHBOURS = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1)
    )

    def __init__(self, initial_state: Optional[Iterable[Tuple[int, int]]]) -> None:
        self.live_cells : Set[Tuple[int, int]] = set(initial_state) if initial_state else set()
        self.generation = 0

    #Basic operations
    def add_cell(self, x: int, y: int) -> None:
        """Add a live cell at (x, y)"""
        self.live_cells.add((x, y))
    
    def remove_cell(self, x: int, y: int) -> None:
        """Remove a live cell at (x, y)"""
        self.live_cells.discard((x, y))
    
    def toggle_cell(self, x: int, y: int) -> None:
        if (x, y) in self.live_cells:
            self.live_cells.remove((x,y))
        else:
            self.live_cells.add((x,y))
    
    def is_alive(self, x: int, y: int) -> bool:
        return (x, y) in self.live_cells
    
    def count_neighbours(self) -> Dict[Tuple[int, int], int]:
        """
        This function doesn't compute the neighbour count of each live cell.
        Instead, each live cell contributes +1 to its 8 surrounding cells
        This indirectly helps us to calculate live neighbours of dead cells, 
        which may become alive in next generation.
        Also indirectly, live cells that don't have any live neighbour never get into the
        dictionary. Nothing to worry as they will die anyways in next generation.
        """
        neighbour_counts : Dict[Tuple[int, int], int] = {}
        for (x, y) in self.live_cells:
            for dx, dy in self._NEIGHBOURS:
                neighbour = (x+dx, y+dy)
                neighbour_counts[neighbour] = neighbour_counts.get(neighbour, 0) + 1
        
        return neighbour_counts


    
    def step(self):
        """
        Advance the universe by one generation
        Apply Conway's Rules
        """
        neighbour_counts: Dict[Tuple[int, int], int] = self.count_neighbours()
        new_live_cells: Set[Tuple[int, int]] = set()

        for cell, count in neighbour_counts.items():
            if cell in self.live_cells:
                if count == 2 or count == 3:
                    #survival rule
                    new_live_cells.add(cell)
                else:
                    #dies due to underpopulation or overpopulation
                    pass
            else:
                if count == 3:
                    #reproduction/birth rule
                    new_live_cells.add(cell)
        
        self.live_cells = new_live_cells
        self.generation += 1

    def population(self) -> int:
        return len(self.live_cells)
    
    def clear(self) -> None:
        """Remove all live cells and reset generation"""
        self.live_cells.clear()
        self.generation = 0
    
    def load_pattern(self, pattern: Iterable[Tuple[int, int]], offset_x:int = 0, offset_y:int = 0) -> None:
        """To load a pattern manually"""
        for x,y in pattern:
            self.live_cells.add((x+offset_x, y+offset_y))
