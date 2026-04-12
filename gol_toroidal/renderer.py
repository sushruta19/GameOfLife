"""
renderer.py - 3D Torus Version with UI, Mouse Picking, and Context Menu (Standard GoL)
"""

import pygame
import math
import multiprocessing as mp
from typing import Tuple, List, Optional
from engine import Universe
from patterns import PATTERNS
from graph import run_graph

def point_in_polygon(pt: Tuple[int, int], poly: List[Tuple[int, int]]) -> bool:
    """Checks if a 2D point is inside a 2D polygon using the Ray-Casting algorithm."""
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
        print("Initializing pygame...")
        pygame.display.init()
        pygame.font.init()
        print("Pygame initialized.")

        self.universe = universe
        info = pygame.display.Info()
        self.width = int(info.current_w * 0.8)
        self.height = int(info.current_h * 0.8)
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Conway's Game of Life - 3D Torus")

        self.clock = pygame.time.Clock()

        # --- 3D Torus Variables ---
        self.R = 160  # Major radius
        self.r = 60   # Minor radius
        self.rot_x = 0.5
        self.rot_y = 0.0
        self.rot_z = 0.0
        self.fov = 400
        self.viewer_distance = 600
        self.grid_points = self._generate_torus_points()
        self.rendered_polygons = [] # Stores projected 2D polygons for mouse picking

        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        
        self.bg_color = (15, 15, 15)
        self.grid_line_color = (50, 50, 65)
        self.cell_color = (0, 200, 120)        # Color for live cells
        self.dead_cell_color = (25, 25, 30)    # Dark gray for solidifying the torus

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

        # --- Original Menu Bar ---
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
        """Generates the static 3D points of the Torus geometry."""
        points = []
        W = getattr(self.universe, 'width', 50)
        H = getattr(self.universe, 'height', 50)
        
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
        """Applies current rotation to a 3D point."""
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        y, z = y * cx - z * sx, y * sx + z * cx
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        x, z = x * cy + z * sy, -x * sy + z * cy
        cz, sz = math.cos(self.rot_z), math.sin(self.rot_z)
        x, y = x * cz - y * sz, x * sz + y * cz
        return x, y, z

    def _project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[int, int]:
        """Projects a 3D point onto the 2D screen."""
        factor = self.fov / (self.viewer_distance + z)
        px = x * factor + self.width / 2
        py = -y * factor + self.height / 2
        return int(px), int(py)

    def display_info(self) -> None:
        population = self.universe.population()
        generation = self.universe.generation
        info_text = (
            f"Gen: {generation}   "
            f"Pop: {population}   "
            f"Speed: {self.gen_per_sec} gen/s   "
            f"Size: {self.universe.width}x{self.universe.height}   "
            f"(Drag: Rotate | R-Click: Toggle | Ctrl+R-Click: Menu)"
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

    def draw_context_menu(self) -> None:
        if not self.context_menu_active:
            return
            
        mx, my = pygame.mouse.get_pos()
        x, y = self.context_menu_pos
        
        # Draw categories
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
            
        # Draw sub-menu for active category
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

    def handle_context_menu_click(self, mx: int, my: int) -> bool:
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
                    # Load the pattern to the cell we Ctrl+Right Clicked on
                    pattern_coords = PATTERNS[category][pattern_name]
                    wx, wy = self.context_world_pos
                    self.universe.load_pattern(pattern_coords, offset_x=wx, offset_y=wy)
                    
                    self.context_menu_active = False
                    self.context_menu_active_category = None
                    return True
                    
        self.context_menu_active = False
        self.context_menu_active_category = None
        return False

    def draw_torus(self) -> None:
        W = getattr(self.universe, 'width', 50)
        H = getattr(self.universe, 'height', 50)
        
        polygons = []

        # Calculate coordinates for all cells
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
                
                is_live = (x, y) in self.universe.live_cells
                polygons.append((avg_z, [proj1, proj2, proj3, proj4], x, y, is_live))

        # Sort polygons from furthest (negative Z) to closest (positive Z)
        polygons.sort(key=lambda item: item[0])
        
        # Store for mouse picking later
        self.rendered_polygons = polygons

        # Draw to screen (Back to Front)
        for avg_z, points, x, y, is_live in polygons:
            # We now fill ALL cells so the torus is a solid object.
            # This hides the back face geometry and makes clicking accurate.
            if is_live:
                pygame.draw.polygon(self.screen, self.cell_color, points)
            else:
                pygame.draw.polygon(self.screen, self.dead_cell_color, points)
            
            if self.show_grid:
                # Anti-aliased lines drastically reduce the wiggly artifacting
                pygame.draw.aalines(self.screen, self.grid_line_color, True, points)

    def draw(self) -> None:
        self.screen.fill(self.bg_color)
        
        self.draw_torus()
        self.draw_menu()
        self.display_info()
        self.draw_context_menu()
        
        pygame.display.flip()

    def _get_clicked_cell(self, mx: int, my: int) -> Optional[Tuple[int, int]]:
        """Helper to find which 3D cell is under the mouse cursor."""
        for avg_z, points, x, y, is_live in reversed(self.rendered_polygons):
            if point_in_polygon((mx, my), points):
                return (x, y)
        return None

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
                
                # Check if clicking inside context menu first
                if self.context_menu_active and event.button in (1, 3):
                    if self.handle_context_menu_click(mx, my):
                        continue
                    self.context_menu_active = False
                    
                if my < self.menu_height:
                    # UI Menu Clicks
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
                                self.graph_queue.put((self.universe.generation, self.universe.population()))
                                self.last_graphed_gen = self.universe.generation
                else:
                    # 3D Area Interaction
                    keys = pygame.key.get_pressed()
                    is_ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

                    if event.button == 3 and is_ctrl_pressed:
                        # Ctrl + Right Click = Context Menu
                        clicked_cell = self._get_clicked_cell(mx, my)
                        if clicked_cell:
                            self.context_menu_active = True
                            self.context_menu_pos = (mx, my)
                            self.context_world_pos = clicked_cell
                            self.paused = True

                    elif event.button == 1:
                        # Left Click = Start dragging to rotate
                        self.is_dragging = True
                        self.last_mouse_pos = (mx, my)
                        
                    elif event.button == 3 and not is_ctrl_pressed:
                        # Right Click = Toggle Cell on Torus
                        clicked_cell = self._get_clicked_cell(mx, my)
                        if clicked_cell:
                            self.paused = True
                            self.universe.toggle_cell(*clicked_cell)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    mx, my = event.pos
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]
                    
                    # Apply rotation
                    self.rot_y -= dx * 0.01
                    self.rot_x -= dy * 0.01
                    
                    self.last_mouse_pos = (mx, my)

            elif event.type == pygame.MOUSEWHEEL:
                # Zoom in / out
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
                            self.graph_queue.put((current_gen, self.universe.population()))
                            self.last_graphed_gen = current_gen
            else:
                self.accumulator = 0.0
            self.draw()

        pygame.quit()