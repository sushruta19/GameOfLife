"""
main.py
"""

from engine import Universe
from renderer import Renderer

if __name__ == "__main__":
    U = Universe(initial_state=None)
    R = Renderer(U)
    R.run()