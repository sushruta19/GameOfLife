"""
main.py
"""

from engine import Universe
from renderer import Renderer

if __name__ == "__main__":
    # Create a 50x50 Toroidal Universe
    U = Universe(width=50, height=50, initial_state=None)
    R = Renderer(U)
    R.run()