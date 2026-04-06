"""
renderer.py (p2life variant)
"""

import pygame
import math
import multiprocessing as mp
from typing import Tuple
from engine import Universe, WHITE, BLACK
from patterns import PATTERNS
from graph import run_graph

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
        pygame.display.set_caption("P2Life: Two-Player Conway's Game of Life - Soubhik")

        self.clock = pygame.time.Clock()

        self.min_cell_size = 1
        self.max_cell_size = 20
        self.cell_size = 20 
        
        self.offset_x = (self.width // 2) - ((self.width // 2) % self.cell_size)
        self.offset_y = (self.height // 2) - ((self.height // 2) % self.cell_size)
        
        self.bg_color = (15, 15, 15)
        self.p1_color = (0, 200, 120)    # Green (WHITE)
        self.p2_color = (200, 40, 40)    # Red   (BLACK)

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

        self.menu_height = 40
        self.menu_bg_color = (50, 50, 50)
        self.button_color = (100, 100, 100)
        self.button_hover_color = (150, 150, 150)
        self.text_color = (255, 255, 255)
        
        self.menu_buttons = {
            "Play/Pause": pygame.Rect(10, 5, 100, 30),
            "Clear": pygame.Rect(120, 5, 80, 30),
            "Toggle Grid": pygame.Rect(210, 5, 100, 30),
            "Speed +": pygame.Rect(320, 5, 80, 30),
            "Speed -": pygame.Rect(410, 5, 80, 30),
            "Graph": pygame.Rect(500, 5, 80, 30)
        }

        # Context Menu
        self.context_menu_active = False
        self.context_menu_pos = (0, 0)
        self.context_world_pos = (0, 0)
        self.context_menu_active_category = None
        
        self.cm_width = 150
        self.cm_item_height = 30
        self.cm_bg_color = (60, 60, 60)
        self.cm_hover_color = (90, 90, 90)
        self.categories = list(PATTERNS.keys())

        # Multiprocessing state variables
        self.graph_process = None
        self.graph_queue = None
        self.last_graphed_gen = -1

    def world_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        sx = x * self.cell_size + self.offset_x
        sy = y * self.cell_size + self.offset_y
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> Tuple[int, int]:
        x = math.floor((sx - self.offset_x) / self.cell_size)
        y = math.floor((sy - self.offset_y) / self.cell_size)        
        return x, y

    def display_info(self) -> None:
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
        pygame.draw.rect(self.screen, self.menu_bg_color, (0, 0, self.width, self.menu_height))
        mx, my = pygame.mouse.get_pos()
        for text, rect in self.menu_buttons.items():
            color = self.button_hover_color if rect.collidepoint(mx, my) else self.button_color
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            text_surf = self.font.render(text, True, self.text_color)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def draw_grid(self) -> None:
        if not self.show_grid or self.cell_size < 5:
            return
        first_vertical = (self.offset_x) % self.cell_size
        for x in range(first_vertical, self.width, self.cell_size):
            pygame.draw.line(self.screen, self.grid_color, (x, 0), (x, self.height))
        first_horizontal = (self.offset_y) % self.cell_size
        for y in range(first_horizontal, self.height, self.cell_size):
            pygame.draw.line(self.screen, self.grid_color, (0, y), (self.width, y))

    def draw_context_menu(self) -> None:
        if not self.context_menu_active:
            return
            
        mx, my = pygame.mouse.get_pos()
        x, y = self.context_menu_pos
        
        for i, category in enumerate(self.categories):
            rect = pygame.Rect(x, y + i * self.cm_item_height, self.cm_width, self.cm_item_height)
            if rect.collidepoint(mx, my):
                self.context_menu_active_category = category
                break
                
        for i, category in enumerate(self.categories):
            rect = pygame.Rect(x, y + i * self.cm_item_height, self.cm_width, self.cm_item_height)
            is_active = (category == self.context_menu_active_category)
            color = self.cm_hover_color if is_active else self.cm_bg_color
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (20, 20, 20), rect, 1)
            text_surf = self.font.render(category + " >", True, self.text_color)
            self.screen.blit(text_surf, (rect.x + 10, rect.y + 7))
            
        if self.context_menu_active_category:
            category = self.context_menu_active_category
            i = self.categories.index(category)
            sub_patterns = list(PATTERNS[category].keys())
            sub_x = x + self.cm_width
            sub_y = y + i * self.cm_item_height
            
            for j, pattern_name in enumerate(sub_patterns):
                p_rect = pygame.Rect(sub_x, sub_y + j * self.cm_item_height, self.cm_width, self.cm_item_height)
                p_color = self.cm_hover_color if p_rect.collidepoint(mx, my) else self.cm_bg_color
                pygame.draw.rect(self.screen, p_color, p_rect)
                pygame.draw.rect(self.screen, (20, 20, 20), p_rect, 1)
                p_surf = self.font.render(pattern_name, True, self.text_color)
                self.screen.blit(p_surf, (p_rect.x + 10, p_rect.y + 7))

    def handle_context_menu_click(self, mx: int, my: int, button: int) -> bool:
        if not self.context_menu_active:
            return False
            
        x, y = self.context_menu_pos
        for i, category in enumerate(self.categories):
            rect = pygame.Rect(x, y + i * self.cm_item_height, self.cm_width, self.cm_item_height)
            if rect.collidepoint(mx, my):
                return True
                
        if self.context_menu_active_category:
            category = self.context_menu_active_category
            i = self.categories.index(category)
            sub_patterns = list(PATTERNS[category].keys())
            sub_x = x + self.cm_width
            sub_y = y + i * self.cm_item_height
            
            for j, pattern_name in enumerate(sub_patterns):
                p_rect = pygame.Rect(sub_x, sub_y + j * self.cm_item_height, self.cm_width, self.cm_item_height)
                if p_rect.collidepoint(mx, my):
                    pattern_coords = PATTERNS[category][pattern_name]
                    wx, wy = self.context_world_pos
                    # Assign player based on left click (Green) or right click (Red)
                    player_color = WHITE if button == 1 else BLACK
                    
                    # Manual injection of pattern, or call load_pattern if you update engine.py to support player argument
                    for (px, py) in pattern_coords:
                        self.universe.live_cells[(wx + px, wy + py)] = player_color
                    
                    self.context_menu_active = False
                    self.context_menu_active_category = None
                    return True
                    
        self.context_menu_active = False
        self.context_menu_active_category = None
        return False
    
    def draw(self) -> None:
        self.screen.fill(self.bg_color)
        self.draw_grid()

        for (x, y), owner in self.universe.live_cells.items():
            sx, sy = self.world_to_screen(x, y)
            rect = pygame.Rect(sx, sy, self.cell_size, self.cell_size)
            if owner == WHITE:
                pygame.draw.rect(self.screen, self.p1_color, rect)
            elif owner == BLACK:
                pygame.draw.rect(self.screen, self.p2_color, rect)
        
        self.draw_menu()
        self.display_info()
        self.draw_context_menu()
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
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.gen_per_sec = min(self.max_gen_per_sec, self.gen_per_sec + 1)
                    self.simulation_interval = 1.0 / self.gen_per_sec
                elif event.key == pygame.K_MINUS:
                    self.gen_per_sec = max(self.min_gen_per_sec, self.gen_per_sec - 1)
                    self.simulation_interval = 1.0 / self.gen_per_sec
                self.context_menu_active = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                if self.context_menu_active and event.button in (1, 3):
                    if self.handle_context_menu_click(mx, my, event.button):
                        continue
                    self.context_menu_active = False
                    
                if my < self.menu_height:
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
                        elif self.menu_buttons["Graph"].collidepoint(mx, my):
                            if self.graph_process is None or not self.graph_process.is_alive():
                                self.graph_queue = mp.Queue()
                                self.graph_process = mp.Process(target=run_graph, args=(self.graph_queue,))
                                self.graph_process.daemon = True
                                self.graph_process.start()
                                p1_pop, p2_pop = self.universe.population()
                                self.graph_queue.put((self.universe.generation, p1_pop, p2_pop))
                                self.last_graphed_gen = self.universe.generation
                else:
                    keys = pygame.key.get_pressed()
                    is_ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
                    
                    if event.button == 3 and is_ctrl_pressed:
                        self.context_menu_active = True
                        self.context_menu_pos = (mx, my)
                        self.context_world_pos = self.screen_to_world(mx, my)
                        self.paused = True
                    
                    elif event.button == 1:
                        self.paused = True
                        x, y = self.screen_to_world(mx, my)
                        self.universe.toggle_cell(x, y, player=WHITE)
                    elif event.button == 3:
                        self.paused = True
                        x, y = self.screen_to_world(mx, my)
                        self.universe.toggle_cell(x, y, player=BLACK)

            elif event.type == pygame.MOUSEWHEEL:
                cx = self.width // 2
                cy = self.height // 2
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
                self.offset_x = int(cx - world_x * self.cell_size)
                self.offset_y = int(cy - world_y * self.cell_size)

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

    def run(self) -> None:
        target_fps = self.target_fps

        while self.running:
            dt = self.clock.tick(target_fps) / 1000.0
            self.handle_events()

            if not self.paused:
                self.accumulator += dt
                while self.accumulator >= self.simulation_interval:
                    self.universe.step()
                    self.accumulator -= self.simulation_interval
                    
                    if self.graph_process and self.graph_process.is_alive():
                        current_gen = self.universe.generation
                        if current_gen != self.last_graphed_gen:
                            p1_pop, p2_pop = self.universe.population()
                            self.graph_queue.put((current_gen, p1_pop, p2_pop))
                            self.last_graphed_gen = current_gen
            else:
                self.accumulator = 0.0
            self.draw()

        pygame.quit()