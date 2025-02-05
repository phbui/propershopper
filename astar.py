import math
import heapq

class AStar:
    def __init__(self, map_data, start, goal, step_size=0.15, max_iter=1000):
        """
        AStar replacement for RRT with the same constructor signature.
        step_size, max_iter, and buffer are unused by A*, but kept for compatibility.
        
        :param map_data: The Map object you already use (with .grid, .rows, .cols, .grid_size).
        :param start: (x, y) float coordinates of the start.
        :param goal: (x, y) float coordinates of the goal.
        """
        self.map_data = map_data
        self.start = tuple(start)
        self.goal = tuple(goal)
        self.step_size = step_size
        self.max_iter = max_iter

        # Access grid info from the map
        self.grid_size = map_data.grid_size
        self.grid = map_data.grid
        self.rows = map_data.rows
        self.cols = map_data.cols

        # Convert float world coords to integer grid coords
        self.start_cell = self.to_grid(self.start)
        self.goal_cell = self.to_grid(self.goal)

    # --------------------------------------------------------------------------
    # GRID / WORLD CONVERSION
    # --------------------------------------------------------------------------
    def to_grid(self, point):
        """
        Convert continuous (x, y) to integer (grid_x, grid_y).
        Each cell is self.grid_size wide/high.
        """
        x, y = point
        gx = int(x // self.grid_size)
        gy = int(y // self.grid_size)
        return (gx, gy)

    def to_world(self, cell):
        """
        Convert integer (grid_x, grid_y) back to a float (x, y) near
        the center of that cell.
        """
        gx, gy = cell
        world_x = (gx + 0.5) * self.grid_size
        world_y = (gy + 0.5) * self.grid_size
        return (world_x, world_y)

    # --------------------------------------------------------------------------
    # COLLISION / OBSTACLE CHECK
    # --------------------------------------------------------------------------
    def is_free_cell(self, gx, gy):
        """
        1) Must be inside the map.
        2) Cell itself must be free, except if it's exactly start or goal cell.
        3) If not near the goal, also ensure no adjacency to obstacles.
        """
        # Boundary
        if gx < 0 or gx >= self.cols or gy < 0 or gy >= self.rows:
            return False

        # If the cell itself is an obstacle:
        if self.grid[gy][gx] != 0:
            # Allow it if it's exactly the start or goal
            if (gx, gy) != self.start_cell and (gx, gy) != self.goal_cell:
                return False

        # If we're not near the goal, ensure we don't touch obstacles
        # (including diagonals).
        if not self.is_goal_or_adjacent(gx, gy) and not self.is_start_or_adjacent(gx,gy):
            neighbors_check = []
            for dx in range(-2, 3):
                for dy in range(-2, 3):  # -2, -1, 0, 1, 2
                    # Skip the cell itself
                    if dx == 0 and dy == 0:
                        continue
                    neighbors_check.append((gx + dx, gy + dy))

            for nx, ny in neighbors_check:
                # Must also check map boundaries for each neighbor
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny][nx] != 0:
                        # If neighbor is an obstacle but not specifically the start/goal
                        if (nx, ny) != self.start_cell and (nx, ny) != self.goal_cell:
                            return False

        return True

    
    def is_goal_or_adjacent(self, gx, gy):
        """
        Return True if (gx, gy) is the goal cell or one of its 8 adjacent cells.
        """
        Gx, Gy = self.goal_cell
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if (gx, gy) == (Gx + dx, Gy + dy):
                    return True
        return False

    def is_start_or_adjacent(self, gx, gy):
        """
        Return True if (gx, gy) is the goal cell or one of its 8 adjacent cells.
        """
        Gx, Gy = self.start_cell
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if (gx, gy) == (Gx + dx, Gy + dy):
                    return True
        return False

    # --------------------------------------------------------------------------
    # A* CORE
    # --------------------------------------------------------------------------
    def heuristic(self, cell_a, cell_b):
        """
        Heuristic for A*. We can use Euclidean distance in grid coordinates.
        For strictly 4-direction movement, Manhattan is also common.
        """
        ax, ay = cell_a
        bx, by = cell_b
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
    
    def run_astar(self, start_cell, goal_cell):
        """
        Standard A* from start_cell to goal_cell (both in grid coords).
        Returns a list of continuous (x, y) points if successful, or None.
        Includes debugging print statements for clarity.
        """
        print(f"Starting A* from {start_cell} to {goal_cell}")

        open_set = []
        came_from = {}
        g_cost = {start_cell: 0.0}

        start_heur = self.heuristic(start_cell, goal_cell)
        heapq.heappush(open_set, (start_heur, 0.0, start_cell))
        came_from[start_cell] = None

        # 4-directionally adjacent
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while open_set:
            # print(f"\nOpen set: {open_set}")
            f, current_g, current_cell = heapq.heappop(open_set)
            # print(f"Expanding cell {current_cell} with f={f}, g={current_g}")

            if current_cell == goal_cell:
                # print("\nGoal reached! Reconstructing path...")
                path = self.reconstruct_path(came_from, current_cell)
                # print(f"Reconstructed path: {path}")
                return path

            # Explore neighbors
            for dx, dy in directions:
                nx = current_cell[0] + dx
                ny = current_cell[1] + dy
                neighbor = (nx, ny)

                if self.is_free_cell(nx, ny):
                    tentative_g = current_g + 1.0  # cost 1 per cell
                    # print(f"  Neighbor {neighbor} is free with tentative_g={tentative_g}")
                    if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                        g_cost[neighbor] = tentative_g
                        f_cost = tentative_g + self.heuristic(neighbor, goal_cell)
                        came_from[neighbor] = current_cell
                        heapq.heappush(open_set, (f_cost, tentative_g, neighbor))
                        # print(f"    Added {neighbor} to open set with f={f_cost}, g={tentative_g}")
                # else:
                    # print(f"  Neighbor {neighbor} is blocked or out of bounds.")

        print("\nNo path found!")
        return None

    def reconstruct_path(self, came_from, current_cell):
        """
        Rebuild path in grid cells; convert to continuous coords.
        """
        path_cells = []
        while current_cell is not None:
            path_cells.append(current_cell)
            current_cell = came_from[current_cell]
        path_cells.reverse()

        # Convert each grid cell to a continuous coordinate near the center
        path_points = [self.to_world(c) for c in path_cells]
        return path_points

    # --------------------------------------------------------------------------
    # FALLBACK: FIND CLOSEST OPEN SPACE VERTICAL
    # --------------------------------------------------------------------------
    def find_closest_open_space_vertical(self, start_cell, goal_cell, max_search_distance=10):
        """
        Scan up and down from the goal_cell on the same X, i.e. same grid_x,
        in increments of 1 cell, up to max_search_distance cells away.
        
        Among all free cells found, pick the one that MINIMIZES:
            distance_to_player + distance_to_goal
        
        :param start_cell: (gx, gy) of the player
        :param goal_cell: (gx, gy) of the exact goal
        :param max_search_distance: how many cells up/down to check
        :return: fallback cell or None if none found
        """
        gx, gy = goal_cell
        sx, sy = start_cell

        best_cell = None
        best_score = float('inf')

        for i in range(max_search_distance + 1):
            # Check upwards
            up_y = gy + i
            if i == 0:
                # i=0 means the goal_cell itself, but if that was free,
                # we would have found a path. We still check it in case
                # it’s free but A* was blocked from some route.
                pass
            if 0 <= up_y < self.rows:
                if self.is_free_cell(gx, up_y):
                    # Score = distance to goal + distance to player
                    dist_player = self.heuristic((gx, up_y), (sx, sy))
                    dist_goal   = self.heuristic((gx, up_y), (gx, gy))
                    score = dist_player + dist_goal
                    if score < best_score:
                        best_score = score
                        best_cell = (gx, up_y)

            # Check downwards
            if i > 0:  # avoid double-checking i=0
                down_y = gy - i
                if 0 <= down_y < self.rows:
                    if self.is_free_cell(gx, down_y):
                        dist_player = self.heuristic((gx, down_y), (sx, sy))
                        dist_goal   = self.heuristic((gx, down_y), (gx, gy))
                        score = dist_player + dist_goal
                        if score < best_score:
                            best_score = score
                            best_cell = (gx, down_y)

        return best_cell

    # --------------------------------------------------------------------------
    # MAIN PLAN METHOD
    # --------------------------------------------------------------------------
    def plan(self):
        """
        1) Try A* to the exact goal.
        2) If no path, find a vertical fallback cell near the goal.
        3) Run A* to the fallback. Return that path or None if fails.
        """
        goal = self.goal_cell
        
        if not self.is_free_cell(goal[0], goal[1]):
            goal = self.find_closest_open_space_vertical(
                start_cell=self.start_cell,
                goal_cell=self.goal_cell,
                max_search_distance=10  # number of grid cells to look up/down
            )
        if goal is None:
            return None  # no fallback found

        path = self.run_astar(self.start_cell, goal)
        return path

    def print_grid(self, start=None, goal=None, player=None, path=None):
        """
        Prints the grid with optional start, goal, player, and path positions.
        Obstacles are shown as '#', free spaces as '.'.
        
        The rendering uses ANSI color codes for clarity:
        - S: Start (blue)
        - G: Goal (red)
        - P: Player (yellow)
        - *: Path (green)
        - .: Free space (white)
        - #: Obstacle (white on black bg)
        
        :param start:   (gx, gy) tuple of the start cell in grid coordinates.
        :param goal:    (gx, gy) tuple of the goal cell in grid coordinates.
        :param player:  (gx, gy) tuple of the player's cell in grid coordinates.
        :param path:    A list or set of (gx, gy) tuples representing a path in grid coords.
        """
        
        # Convert path to a set for O(1) membership checks
        path_set = set(self.to_grid(point) for point in path) if path else set()
        
        rows, cols = self.grid.shape  # Get dimensions from the grid's shape

        for y in range(rows):
            row_output = []
            for x in range(cols):
                cell = (x, y)
                
                # Priority: Start/Goal > Player > Path > Obstacle/Free
                if cell == self.to_grid(start):
                    # Blue S
                    row_output.append("\033[94mS\033[0m")
                elif cell == self.to_grid(goal):
                    # Red G
                    row_output.append("\033[91mG\033[0m")
                elif cell == self.to_grid(player):
                    # Yellow P
                    row_output.append("\033[93mP\033[0m")
                elif cell in path_set:
                    # Green *
                    row_output.append("\033[92m*\033[0m")
                else:
                    # Obstacle or free space
                    if self.grid[y, x] == 0:
                        # White .
                        row_output.append("\033[97m.\033[0m")
                    else:
                        # White # on black background
                        row_output.append("\033[40m#\033[0m")
            print("".join(row_output))
