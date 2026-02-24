"""
renderer.py
"""

import pygame
from typing import Tuple
from engine import Universe

class Renderer:
    def __init__(self, universe: Universe) -> None:
        print("Initializing pygame...")
        pygame.display.init()
        pygame.font.init()
        print("Pygame initialized.")

        self.universe = universe
        info = pygame.display.Info()
        self.width = int(info.current_w*0.8)
        self.height = int(info.current_h*0.8)
        
        print("Creating window...")
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE    
        )
        print("Window created.")
        pygame.display.set_caption("Conway's Game of Life")

        self.clock = pygame.time.Clock()

        self.cell_size = 20 #20px height 20px width
        self.offset_x = self.width // 2
        self.offset_y = self.height // 2

        self.bg_color = (15, 15, 15)
        self.cell_color = (0, 200, 120)

        self.simulation_interval = 0.5 # seconds per generation(2 gen / sec)
        self.accumulator = 0.0

        self.running = True
        self.paused = True

        self.font = pygame.font.Font(None, 20)
    
    def world_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        sx = x*self.cell_size + self.offset_x
        sy = y*self.cell_size + self.offset_y
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> Tuple[int, int]:
        x = (sx - self.offset_x) // self.cell_size
        y = (sy - self.offset_y) // self.cell_size        
        return x, y

    def display_info(self) -> None:
        """Display Info about population, generation etc"""
        population = self.universe.population()
        generation = self.universe.generation

        info_text = (
            f"Generation: {generation}   "
            f"Population: {population}   "
            f"Speed: {1/self.simulation_interval:.2f} gen/s"
        )
        text_surface = self.font.render(info_text, True, (200, 200, 200))
        self.screen.blit(text_surface, (10, 10))
        
    def draw(self) -> None:
        self.screen.fill(self.bg_color)

        for (x, y) in self.universe.live_cells:
            sx, sy = self.world_to_screen(x, y)
            rect = pygame.Rect(sx, sy, self.cell_size, self.cell_size)
            pygame.draw.rect(self.screen, self.cell_color, rect)
        self.display_info()
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
                    self.paused = True
                    self.universe.clear()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.paused = True
                mx, my = pygame.mouse.get_pos()
                x, y = self.screen_to_world(mx, my)
                self.universe.toggle_cell(x, y)
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.offset_x = self.width // 2
                self.offset_y = self.height // 2

    def run(self) -> None:
        target_fps = 30

        while self.running:
            # how much time last frame took(ms->s)
            dt = self.clock.tick(target_fps)/1000.0

            self.handle_events()

            if not self.paused:
                self.accumulator += dt
                while self.accumulator >= self.simulation_interval:
                    self.universe.step()
                    self.accumulator -= self.simulation_interval
            else:
                self.accumulator = 0.0
            self.draw()

        pygame.quit()