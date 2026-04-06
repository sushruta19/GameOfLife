"""
renderer.py - 3D Torus Projection Renderer
"""
import pygame
import math
import multiprocessing as mp
from typing import Tuple, List
from engine import Universe
from patterns import PATTERNS
from graph import run_graph

class Renderer:
    def __init__(self, universe: Universe) -> None:
        pygame.display.init()
        pygame.font.init()

        self.universe = universe
        info = pygame.display.Info()
        self.width = int(info.current_w * 0.8)
        self.height = int(info.current_h * 0.8)
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Conway's Game of Life - 3D Torus")
        self.clock = pygame.time.Clock()

        self.bg_color = (15, 15, 15)
        self.cell_color = (0, 255, 150)
        self.dead_cell_color = (30, 30, 40)
        self.grid_line_color = (50, 50, 60)
        
        # --- 3D Projection & Torus Math Variables ---
        self.R = 150  # Major radius (distance from center of donut to center of tube)
        self.r = 60   # Minor radius (radius of the tube itself)
        
        self.rot_x = 0.5  # Initial X rotation
        self.rot_y = 0.0  # Initial Y rotation
        self.rot_z = 0.0  # Initial Z rotation
        
        self.fov = 400
        self.viewer_distance = 600
        
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Generate the base 3D coordinates for the grid points
        self.grid_points = self._generate_torus_points()

        # --- Simulation Control Variables ---
        self.gen_per_sec = 2
        self.simulation_interval = 1.0 / self.gen_per_sec
        self.accumulator = 0.0
        self.running = True
        self.paused = True
        self.target_fps = 30
        self.font = pygame.font.Font(None, 24)

        # Graph Process
        self.graph_process = None
        self.graph_queue = None
        self.last_graphed_gen = -1

    def _generate_torus_points(self) -> List[List[Tuple[float, float, float]]]:
        """Calculates the local 3D coordinates for every grid intersection on the torus."""
        points = []
        W = self.universe.width
        H = self.universe.height
        
        for x in range(W):
            col = []
            # theta is the angle around the main hole (longitude)
            theta = (x / W) * 2 * math.pi
            for y in range(H):
                # phi is the angle around the tube itself (latitude)
                phi = (y / H) * 2 * math.pi
                
                # Parametric equations of a torus
                px = (self.R + self.r * math.cos(phi)) * math.cos(theta)
                py = (self.R + self.r * math.cos(phi)) * math.sin(theta)
                pz = self.r * math.sin(phi)
                
                col.append((px, py, pz))
            points.append(col)
        return points

    def _rotate_3d(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Applies 3D rotation matrices to a point based on mouse drag angles."""
        # Rotate X
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        y, z = y * cx - z * sx, y * sx + z * cx
        # Rotate Y
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        x, z = x * cy + z * sy, -x * sy + z * cy
        # Rotate Z
        cz, sz = math.cos(self.rot_z), math.sin(self.rot_z)
        x, y = x * cz - y * sz, x * sz + y * cz
        return x, y, z

    def _project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[int, int]:
        """Projects a 3D coordinate onto the 2D screen."""
        factor = self.fov / (self.viewer_distance + z)
        px = x * factor + self.width / 2
        py = -y * factor + self.height / 2
        return int(px), int(py)

    def draw(self) -> None:
        self.screen.fill(self.bg_color)
        
        W = self.universe.width
        H = self.universe.height
        
        polygons = []

        # 1. Transform all points and calculate depth (Z) for sorting
        for x in range(W):
            for y in range(H):
                # Get the 4 corners of the current cell
                p1 = self.grid_points[x][y]
                p2 = self.grid_points[(x + 1) % W][y]
                p3 = self.grid_points[(x + 1) % W][(y + 1) % H]
                p4 = self.grid_points[x][(y + 1) % H]
                
                # Rotate all 4 points
                r1 = self._rotate_3d(*p1)
                r2 = self._rotate_3d(*p2)
                r3 = self._rotate_3d(*p3)
                r4 = self._rotate_3d(*p4)
                
                # Average Z of the 4 corners to determine drawing order (Painter's Algorithm)
                avg_z = (r1[2] + r2[2] + r3[2] + r4[2]) / 4.0
                
                # Project to 2D screen coordinates
                proj1 = self._project_3d_to_2d(*r1)
                proj2 = self._project_3d_to_2d(*r2)
                proj3 = self._project_3d_to_2d(*r3)
                proj4 = self._project_3d_to_2d(*r4)
                
                is_live = (x, y) in self.universe.live_cells
                polygons.append((avg_z, [proj1, proj2, proj3, proj4], is_live))

        # 2. Sort polygons by depth (furthest away gets drawn first)
        # In our coordinate system, a more negative Z is further away.
        polygons.sort(key=lambda item: item[0])

        # 3. Draw the polygons
        for avg_z, points, is_live in polygons:
            color = self.cell_color if is_live else self.dead_cell_color
            
            # Fill the cell
            pygame.draw.polygon(self.screen, color, points)
            # Draw wireframe boundary
            pygame.draw.polygon(self.screen, self.grid_line_color, points, 1)

        # 4. Draw simple UI overlay
        status = "PLAYING" if not self.paused else "PAUSED"
        info_text = f"Gen: {self.universe.generation} | Pop: {self.universe.population()} | State: {status} | Space: Play/Pause | C: Clear | Drag Mouse: Rotate 3D"
        text_surf = self.font.render(info_text, True, (255, 255, 255))
        self.screen.blit(text_surf, (10, 10))

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
                if event.button == 1:  # Left Click = Drag to Rotate
                    self.is_dragging = True
                    self.last_mouse_pos = pygame.mouse.get_pos()
                elif event.button == 4: # Mouse Wheel Up = Zoom In
                    self.fov += 20
                elif event.button == 5: # Mouse Wheel Down = Zoom Out
                    self.fov = max(50, self.fov - 20)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    mx, my = event.pos
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]
                    
                    # Convert mouse movement to 3D rotation angles
                    self.rot_y -= dx * 0.01
                    self.rot_x -= dy * 0.01
                    
                    self.last_mouse_pos = (mx, my)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            self.handle_events()

            if not self.paused:
                self.accumulator += dt
                while self.accumulator >= self.simulation_interval:
                    self.universe.step()
                    self.accumulator -= self.simulation_interval

            self.draw()

        pygame.quit()