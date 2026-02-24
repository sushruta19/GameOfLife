"""
renderer.py
"""

import pygame
from typing import Tuple
from engine import Universe

class Renderer:
    def __init__(self, universe: Universe, width: int = 1000, height:int = 800) -> None:
        pygame.init()
        self.universe = universe
        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Conway's Game of Life")

        self.clock = pygame.time.Clock()

        self.cell_size = 20 #20px height 20px width
        self.offset_x = width // 2
        self.offset_y = height // 2

        self.bg_color = (15, 15, 15)
        self.cell_color = (0, 200, 120)

        self.simulation_interval = 0.5 # seconds per generation(2 gen / sec)
        self.accumulator = 0.0

        self.running = True
        self.paused = True
    
    def world_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        sx = x*self.cell_size + self.offset_x
        sy = y*self.cell_size + self.offset_y
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> Tuple[int, int]:
        x = (sx - self.offset_x) // self.cell_size
        y = (sy - self.offset_y) // self.cell_size        
        return x, y

    def draw(self) -> None:
        self.screen.fill(self.bg_color)

        for (x, y) in self.universe.live_cells:
            sx, sy = self.world_to_screen(x, y)
            rect = pygame.Rect(sx, sy, self.cell_size, self.cell_size)
            pygame.draw.rect(self.screen, self.cell_color, rect)
        
        #bringing all changes to actual screen display
        pygame.display.flip()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_c:
                    self.universe.clear()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                x, y = self.screen_to_world(mx, my)
                self.universe.toggle_cell(x, y)

    def run(self) -> None:
        target_fps = 30

        while self.running:
            # how much time last frame took(ms->s)
            dt = self.clock.tick(target_fps)/1000.0
            self.accumulator += dt

            self.handle_events()

            if not self.paused:
                while self.accumulator >= self.simulation_interval:
                    self.universe.step()
                    self.accumulator -= self.simulation_interval
            self.draw()

        pygame.quit()