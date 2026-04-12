"""
renderer.py (p2life_toroidal variant) - 3D Solid Torus Version with UI & Mouse Picking
"""

import pygame
import math
import multiprocessing as mp
from typing import Tuple, List, Optional
from engine import Universe, WHITE, BLACK
from patterns import PATTERNS
from graph import run_graph

def point_in_polygon(pt: Tuple[int, int], poly: List[Tuple[int, int]]) -> bool:
    x, y = pt
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class Renderer:
    def __init__(self, universe: Universe) -> None:
        pygame.display.init()
        pygame.font.init()

        self.universe = universe
        info = pygame.display.Info()
        self.width = int(info.current_w * 0.8)
        self.height = int(info.current_h * 0.8)
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("P2Life: Two-Player 3D Torus - Soubhik")
        self.clock = pygame.time.Clock()

        # --- 3D Torus Variables ---
        self.R = 160
        self.r = 60
        self.rot_x = 0.5
        self.rot_y = 0.0
        self.rot_z = 0.0
        self.fov = 400
        self.viewer_distance = 600
        self.grid_points = self._generate_torus_points()
        self.rendered_polygons = []

        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Colors
        self.bg_color = (15, 15, 15)
        self.grid_line_color = (50, 50, 65)
        self.p1_color = (0, 200, 120)       # Green (WHITE)
        self.p2_color = (200, 40, 40)       # Red   (BLACK)
        self.dead_cell_color = (25, 25, 30) # Dark gray (Solid Torus)

        # --- Simulation Variables ---
        self.gen_per_sec = 2
        self.min_gen_per_sec = 1
        self.max_gen_per_sec = 50
        self.simulation_interval = 1.0 / self.gen_per_sec
        self.accumulator = 0.0
        self.running = True
        self.paused = True
        self.font = pygame.font.Font(None, 20)
        self.show_grid = True
        self.target_fps = 30

        # --- UI Variables ---
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

        # --- Context Menu ---
        self.context_menu_active = False
        self.context_menu_pos = (0, 0)
        self.context_world_pos = (0, 0)
        self.context_menu_active_category = None
        self.cm_width = 150
        self.cm_item_height = 30
        self.cm_bg_color = (60, 60, 60)
        self.cm_hover_color = (90, 90, 90)
        self.categories = list(PATTERNS.keys())

        # --- Graph Process ---
        self.graph_process = None
        self.graph_queue = None
        self.last_graphed_gen = -1

    def _generate_torus_points(self) -> List[List[Tuple[float, float, float]]]:
        points = []
        W = self.universe.width
        H = self.universe.height
        
        for x in range(W):
            col = []
            theta = (x / W) * 2 * math.pi
            for y in range(H):
                phi = (y / H) * 2 * math.pi
                px = (self.R + self.r * math.cos(phi)) * math.cos(theta)
                py = (self.R + self.r * math.cos(phi)) * math.sin(theta)
                pz = self.r * math.sin(phi)
                col.append((px, py, pz))
            points.append(col)
        return points

    def _rotate_3d(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        y, z = y * cx - z * sx, y * sx + z * cx
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        x, z = x * cy + z * sy, -x * sy + z * cy
        cz, sz = math.cos(self.rot_z), math.sin(self.rot_z)
        x, y = x * cz - y * sz, x * sz + y * cz
        return x, y, z

    def _project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[int, int]:
        factor = self.fov / (self.viewer_distance + z)
        px = x * factor + self.width / 2
        py = -y * factor + self.height / 2
        return int(px), int(py)

    def display_info(self) -> None:
        p1_pop, p2_pop = self.universe.population()
        generation = self.universe.generation
        info_text = (
            f"Gen: {generation}   "
            f"Green: {p1_pop}   "
            f"Red: {p2_pop}   "
            f"Speed: {self.gen_per_sec} gen/s   "
            f"(Drag: Rotate | Shift+LClick: Green | RClick: Red | Ctrl+Click: Menu)"
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

    def draw_torus(self) -> None:
        W = self.universe.width
        H = self.universe.height
        polygons = []

        for x in range(W):
            for y in range(H):
                p1 = self.grid_points[x][y]
                p2 = self.grid_points[(x + 1) % W][y]
                p3 = self.grid_points[(x + 1) % W][(y + 1) % H]
                p4 = self.grid_points[x][(y + 1) % H]
                
                r1 = self._rotate_3d(*p1)
                r2 = self._rotate_3d(*p2)
                r3 = self._rotate_3d(*p3)
                r4 = self._rotate_3d(*p4)
                
                avg_z = (r1[2] + r2[2] + r3[2] + r4[2]) / 4.0
                
                proj1 = self._project_3d_to_2d(*r1)
                proj2 = self._project_3d_to_2d(*r2)
                proj3 = self._project_3d_to_2d(*r3)
                proj4 = self._project_3d_to_2d(*r4)
                
                owner = self.universe.live_cells.get((x, y))
                polygons.append((avg_z, [proj1, proj2, proj3, proj4], x, y, owner))

        # Back-to-front sorting (Painter's Algorithm)
        polygons.sort(key=lambda item: item[0])
        self.rendered_polygons = polygons

        for avg_z, points, x, y, owner in polygons:
            if owner == WHITE:
                pygame.draw.polygon(self.screen, self.p1_color, points)
            elif owner == BLACK:
                pygame.draw.polygon(self.screen, self.p2_color, points)
            else:
                pygame.draw.polygon(self.screen, self.dead_cell_color, points)
            
            if self.show_grid:
                pygame.draw.aalines(self.screen, self.grid_line_color, True, points)

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
                    # Left Click menu = Green pattern, Right Click menu = Red pattern
                    player_color = WHITE if button == 1 else BLACK
                    
                    self.universe.load_pattern(pattern_coords, player_color, offset_x=wx, offset_y=wy)
                    self.context_menu_active = False
                    self.context_menu_active_category = None
                    return True
                    
        self.context_menu_active = False
        self.context_menu_active_category = None
        return False

    def _get_clicked_cell(self, mx: int, my: int) -> Optional[Tuple[int, int]]:
        for avg_z, points, x, y, owner in reversed(self.rendered_polygons):
            if point_in_polygon((mx, my), points):
                return (x, y)
        return None

    def draw(self) -> None:
        self.screen.fill(self.bg_color)
        self.draw_torus()
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
                    is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                    
                    if event.button in (1, 3) and is_ctrl_pressed:
                        clicked_cell = self._get_clicked_cell(mx, my)
                        if clicked_cell:
                            self.context_menu_active = True
                            self.context_menu_pos = (mx, my)
                            self.context_world_pos = clicked_cell
                            self.paused = True
                            
                    elif event.button == 1 and not is_shift_pressed:
                        # Drag to pan/rotate
                        self.is_dragging = True
                        self.last_mouse_pos = (mx, my)
                        
                    elif event.button == 1 and is_shift_pressed:
                        # Toggle Green (P1)
                        clicked_cell = self._get_clicked_cell(mx, my)
                        if clicked_cell:
                            self.paused = True
                            self.universe.toggle_cell(*clicked_cell, player=WHITE)
                            
                    elif event.button == 3 and not is_ctrl_pressed:
                        # Toggle Red (P2)
                        clicked_cell = self._get_clicked_cell(mx, my)
                        if clicked_cell:
                            self.paused = True
                            self.universe.toggle_cell(*clicked_cell, player=BLACK)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    mx, my = event.pos
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]
                    self.rot_y -= dx * 0.01
                    self.rot_x -= dy * 0.01
                    self.last_mouse_pos = (mx, my)

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.fov += 20
                else:
                    self.fov = max(50, self.fov - 20)

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