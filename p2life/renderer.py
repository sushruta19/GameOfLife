"""
renderer.py (p2life variant)
"""

import pygame
import math
from typing import Tuple
from engine import Universe, WHITE, BLACK

class Renderer:
    def __init__(self, universe: Universe) -> None:
        print("Initializing pygame...")
        pygame.display.init()
        pygame.font.init()
        print("Pygame initialized.")

        self.universe = universe
        info = pygame.display.Info()
        self.width = int(info.current_w * 0.8)
        self.height = int(info.current_h * 0.8)
        
        print("Creating window...")
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE    
        )
        print("Window created.")
        pygame.display.set_caption("P2Life: Two-Player Conway's Game of Life")

        self.clock = pygame.time.Clock()

        self.min_cell_size = 1
        self.max_cell_size = 20
        self.cell_size = 20 
        
        # forces offsets to align with grid boundaries
        self.offset_x = (self.width // 2) - ((self.width // 2) % self.cell_size)
        self.offset_y = (self.height // 2) - ((self.height // 2) % self.cell_size)
        
        self.bg_color = (15, 15, 15)
        
        # We define two colors now instead of one
        self.p1_color = (0, 200, 120)    # Green (Maps to WHITE in engine)
        self.p2_color = (200, 40, 40)    # Red   (Maps to BLACK in engine)

        self.gen_per_sec = 2
        self.min_gen_per_sec = 1
        self.max_gen_per_sec = 50
        self.simulation_interval = 1.0 / self.gen_per_sec
        self.accumulator = 0.0

        self.running = True
        self.paused = True

        self.font = pygame.font.Font(None, 20)

        self.grid_color = (40, 40, 40)
        self.show_grid = True

        self.target_fps = 30

        # Menu bar variables and button definitions
        self.menu_height = 40
        self.menu_bg_color = (50, 50, 50)
        self.button_color = (100, 100, 100)
        self.button_hover_color = (150, 150, 150)
        self.text_color = (255, 255, 255)
        
        # Define button rectangles (x, y, width, height)
        self.menu_buttons = {
            "Play/Pause": pygame.Rect(10, 5, 100, 30),
            "Clear": pygame.Rect(120, 5, 80, 30),
            "Toggle Grid": pygame.Rect(210, 5, 100, 30),
            "Speed +": pygame.Rect(320, 5, 80, 30),
            "Speed -": pygame.Rect(410, 5, 80, 30)
        }

    def world_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        sx = x * self.cell_size + self.offset_x
        sy = y * self.cell_size + self.offset_y
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> Tuple[int, int]:
        x = math.floor((sx - self.offset_x) / self.cell_size)
        y = math.floor((sy - self.offset_y) / self.cell_size)        
        return x, y

    def display_info(self) -> None:
        """Display Info about population, generation etc"""
        # Population now returns two values!
        p1_pop, p2_pop = self.universe.population()
        generation = self.universe.generation
        target_fps = self.target_fps
        info_text = (
            f"Gen: {generation}   "
            f"Green: {p1_pop}   "
            f"Red: {p2_pop}   "
            f"Speed: {self.gen_per_sec} gen/s   "
            f"FPS: {target_fps}   "
        )
        text_surface = self.font.render(info_text, True, (200, 200, 200))
        self.screen.blit(text_surface, (10, self.menu_height + 10))
    
    def draw_menu(self) -> None:
        # Draw menu background
        pygame.draw.rect(self.screen, self.menu_bg_color, (0, 0, self.width, self.menu_height))
        
        mx, my = pygame.mouse.get_pos()
        
        # Draw buttons
        for text, rect in self.menu_buttons.items():
            # Apply hover effect if mouse is over the button
            color = self.button_hover_color if rect.collidepoint(mx, my) else self.button_color
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            
            # Render text centered in the button
            text_surf = self.font.render(text, True, self.text_color)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def draw_grid(self) -> None:
        if not self.show_grid or self.cell_size < 5:
            return
        # Vertical lines
        first_vertical = (self.offset_x) % self.cell_size
        for x in range(first_vertical, self.width, self.cell_size):
            pygame.draw.line(
                self.screen,
                self.grid_color,
                (x, 0),
                (x, self.height)
            )

        # Horizontal lines
        first_horizontal = (self.offset_y) % self.cell_size
        for y in range(first_horizontal, self.height, self.cell_size):
            pygame.draw.line(
                self.screen,
                self.grid_color,
                (0, y),
                (self.width, y)
            )

    def draw(self) -> None:
        self.screen.fill(self.bg_color)
        self.draw_grid()

        # Render cells based on who owns them
        for (x, y), owner in self.universe.live_cells.items():
            sx, sy = self.world_to_screen(x, y)
            rect = pygame.Rect(sx, sy, self.cell_size, self.cell_size)
            
            if owner == WHITE:
                pygame.draw.rect(self.screen, self.p1_color, rect)
            elif owner == BLACK:
                pygame.draw.rect(self.screen, self.p2_color, rect)
        
        self.draw_menu()
        self.display_info()
        # bringing all changes to actual screen display
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
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Increase simulation speed
                    self.gen_per_sec = min(self.max_gen_per_sec, self.gen_per_sec + 1)
                    self.simulation_interval = 1.0 / self.gen_per_sec
                elif event.key == pygame.K_MINUS:
                    # Decrease simulation speed
                    self.gen_per_sec = max(self.min_gen_per_sec, self.gen_per_sec - 1)
                    self.simulation_interval = 1.0 / self.gen_per_sec

            # Handle mouse clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Check if click is in the menu area
                if my < self.menu_height:
                    # Only left clicks interact with menu buttons
                    if event.button == 1:
                        if self.menu_buttons["Play/Pause"].collidepoint(mx, my):
                            self.paused = not self.paused
                        elif self.menu_buttons["Clear"].collidepoint(mx, my):
                            self.paused = True
                            self.universe.clear()
                        elif self.menu_buttons["Toggle Grid"].collidepoint(mx, my):
                            self.show_grid = not self.show_grid
                        elif self.menu_buttons["Speed +"].collidepoint(mx, my):
                            self.gen_per_sec = min(self.max_gen_per_sec, self.gen_per_sec + 1)
                            self.simulation_interval = 1.0 / self.gen_per_sec
                        elif self.menu_buttons["Speed -"].collidepoint(mx, my):
                            self.gen_per_sec = max(self.min_gen_per_sec, self.gen_per_sec - 1)
                            self.simulation_interval = 1.0 / self.gen_per_sec
                else:
                    # Handle grid cell toggling if click is below the menu bar
                    self.paused = True
                    x, y = self.screen_to_world(mx, my)
                    
                    if event.button == 1:
                        # Left Click -> Toggle Green (WHITE)
                        self.universe.toggle_cell(x, y, player=WHITE)
                    elif event.button == 3:
                        # Right Click -> Toggle Red (BLACK)
                        self.universe.toggle_cell(x, y, player=BLACK)

            elif event.type == pygame.MOUSEWHEEL:
                # screen center
                cx = self.width // 2
                cy = self.height // 2

                # World coordinate at screen center BEFORE zoom
                world_x = (cx - self.offset_x) / self.cell_size
                world_y = (cy - self.offset_y) / self.cell_size

                zoom_factor = 1.1

                if event.y > 0:
                    new_size = min(max(1, round(self.cell_size * zoom_factor)), self.max_cell_size)
                else:
                    new_size = max(round(self.cell_size / zoom_factor), self.min_cell_size)
                if new_size == self.cell_size:
                    return

                self.cell_size = new_size

                # Recalculate offset so center stays stable
                self.offset_x = int(cx - world_x * self.cell_size)
                self.offset_y = int(cy - world_y * self.cell_size)

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

    def run(self) -> None:
        target_fps = self.target_fps

        while self.running:
            # how much time last frame took(ms->s)
            dt = self.clock.tick(target_fps) / 1000.0

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