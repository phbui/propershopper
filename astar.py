import math
import heapq

class AStar:
    def __init__(self, map_data, start, goal, step_size=0.15, max_iter=1000, buffer=0.6):
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
        self.buffer = buffer

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
        Check if the cell is inside the map and not an obstacle (grid == 0).
        """

        if (gx, gy) == self.start_cell or (gx, gy) == self.goal_cell:
            return True 

        if gx < 0 or gx >= self.cols or gy < 0 or gy >= self.rows:
            return False
        
        return (self.grid[gy][gx] == 0)

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

    def print_grid(self, start=None, goal=None):
        """
        Prints the grid with optional start and goal positions.
        Obstacles are shown as '#', free spaces as '.', start as 'S', and goal as 'G'.

        :param grid: 2D numpy array representing the map.
        :param start: (gx, gy) tuple of the start cell in grid coordinates.
        :param goal: (gx, gy) tuple of the goal cell in grid coordinates.
        """
        rows, cols = self.grid.shape  # Get dimensions from the grid's shape

        for y in range(rows):
            row_output = []
            for x in range(self.grid.shape[1]):
                if start == (x, y):
                    row_output.append("S")  # Start
                elif goal == (x, y):
                    row_output.append("G")  # Goal
                elif self.grid[y, x] == 0:
                    row_output.append(".")  # Free space
                else:
                    row_output.append("#")  # Obstacle
            print("".join(row_output))