"""
engine.py (p2life variant)
Simulation Engine for Two-Player Conway's Game of Life (p2life)
"""
import random
from typing import Tuple, Dict, Iterable, Optional

# Define our players/colors
WHITE = 1
BLACK = 2

class Universe:
    """
    Represents an infinite Grid by storing the live cells in a Dictionary.
    Unlike standard GoL, we need to know WHO occupies the cell.
    
    Attributes
    live_cells : Dict[Tuple[int, int], int]
        Maps coordinates to the player occupying it (WHITE or BLACK)
    generation : int
        Current generation count
    """
    # Neighbour coords
    _NEIGHBOURS = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),  (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    )

    def __init__(self, initial_state: Optional[Dict[Tuple[int, int], int]] = None) -> None:
        # We use a dict now instead of a set to track who owns the cell
        self.live_cells: Dict[Tuple[int, int], int] = initial_state.copy() if initial_state else {}
        self.generation = 0

    # Basic operations
    def add_cell(self, x: int, y: int, player: int = WHITE) -> None:
        """Add a live cell for a specific player at (x, y)"""
        self.live_cells[(x, y)] = player
    
    def remove_cell(self, x: int, y: int) -> None:
        """Remove a live cell at (x, y) regardless of color"""
        self.live_cells.pop((x, y), None)
    
    def toggle_cell(self, x: int, y: int, player: int = WHITE) -> None:
        """
        Toggle a cell. If it's empty, add the given player.
        If it's already occupied (by anyone), remove it.
        """
        if (x, y) in self.live_cells:
            del self.live_cells[(x, y)]
        else:
            self.live_cells[(x, y)] = player
    
    def is_alive(self, x: int, y: int) -> bool:
        return (x, y) in self.live_cells
    
    def get_cell_owner(self, x: int, y: int) -> Optional[int]:
        """Returns WHITE, BLACK, or None if empty"""
        return self.live_cells.get((x, y))

    def count_neighbours(self) -> Dict[Tuple[int, int], Dict[int, int]]:
        """
        This calculates how many WHITE and BLACK neighbours each cell has.
        Returns a dictionary mapped to another dictionary:
        { (x, y): {WHITE: 2, BLACK: 1}, ... }
        """
        neighbour_counts: Dict[Tuple[int, int], Dict[int, int]] = {}
        
        for (x, y), owner in self.live_cells.items():
            for dx, dy in self._NEIGHBOURS:
                neighbour = (x + dx, y + dy)
                
                # Initialize the inner dictionary for this neighbour if it doesn't exist
                if neighbour not in neighbour_counts:
                    neighbour_counts[neighbour] = {WHITE: 0, BLACK: 0}
                
                # The owner of the current cell contributes +1 to the neighbour's count
                neighbour_counts[neighbour][owner] += 1
        
        return neighbour_counts

    def step(self):
        """
        Advance the universe by one generation using p2life competitive rules.
        """
        neighbour_counts = self.count_neighbours()
        new_live_cells: Dict[Tuple[int, int], int] = {}

        for cell, counts in neighbour_counts.items():
            w = counts[WHITE]
            b = counts[BLACK]
            
            # --- SURVIVAL RULES ---
            if cell in self.live_cells:
                owner = self.live_cells[cell]
                
                if owner == WHITE:
                    diff = w - b
                    # Rule 1: Net difference is 2 or 3
                    if diff == 2 or diff == 3:
                        new_live_cells[cell] = WHITE
                    # Rule 2: Net difference is 1, and there are at least 2 friendly neighbours
                    elif diff == 1 and w >= 2:
                        new_live_cells[cell] = WHITE
                    # Otherwise, it dies (Implicit underpopulation/overpopulation or defeated)
                
                elif owner == BLACK:
                    diff = b - w
                    # Rule 1 for Black: Net difference is 2 or 3
                    if diff == 2 or diff == 3:
                        new_live_cells[cell] = BLACK
                    # Rule 2 for Black: Net difference is 1, and at least 2 friendly neighbours
                    elif diff == 1 and b >= 2:
                        new_live_cells[cell] = BLACK

            # --- BIRTH RULES (Cell is empty) ---
            else:
                # Rule 1 for White: Exactly 3 White, and Black is NOT 3
                if w == 3 and b != 3:
                    new_live_cells[cell] = WHITE
                
                # Rule 1 for Black: Exactly 3 Black, and White is NOT 3
                elif b == 3 and w != 3:
                    new_live_cells[cell] = BLACK
                
                # Rule 2: Tie! Exactly 3 White AND 3 Black -> Unbiased coin flip
                elif w == 3 and b == 3:
                    winner = random.choice([WHITE, BLACK])
                    new_live_cells[cell] = winner
        
        # Advance the state
        self.live_cells = new_live_cells
        self.generation += 1

    def population(self) -> Tuple[int, int]:
        """Returns the population as a tuple: (white_count, black_count)"""
        white_count = sum(1 for owner in self.live_cells.values() if owner == WHITE)
        black_count = len(self.live_cells) - white_count
        return white_count, black_count
    
    def clear(self) -> None:
        """Remove all live cells and reset generation"""
        self.live_cells.clear()
        self.generation = 0
    
    def load_pattern(self, pattern: Iterable[Tuple[int, int, int]], offset_x:int = 0, offset_y:int = 0) -> None:
        """
        To load a pattern manually. 
        Pattern must now include the owner: [(x, y, player_id), ...]
        """
        for x, y, player_id in pattern:
            self.live_cells[(x + offset_x, y + offset_y)] = player_id
