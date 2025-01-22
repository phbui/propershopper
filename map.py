import numpy as np  # type: ignore
import heapq
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Map:
    def __init__(self, data, grid_size=0.25, player_size=(0.25, 0.25)):
        self.grid_size = grid_size
        self.data = data
        self.player_width, self.player_height = player_size
        self.grid = self.construct_map()
        self.rows, self.cols = self.grid.shape
        logging.debug("Map initialized.")
        self.print_map()

    def construct_map(self):
        all_positions = []
        for entity_type in ["players", "registers", "shelves", "cartReturns", "basketReturns", "counters", "carts", "baskets"]:
            for entity in self.data.get(entity_type, []):
                x, y = entity["position"]
                w, h = entity["width"], entity["height"]
                all_positions.append((x, y))
                all_positions.append((x + w, y + h))
                logging.info(f"Found {entity_type} at position ({x}, {y}) with width {w} and height {h}.")

        max_x = max(pos[0] for pos in all_positions)
        max_y = max(pos[1] for pos in all_positions)

        self.rows = int(np.ceil(max_y / self.grid_size))
        self.cols = int(np.ceil(max_x / self.grid_size))

        grid = np.zeros((self.rows, self.cols))
        self.update_grid(grid, self.data)
        return grid

    def to_grid_coordinates(self, position):
        x, y = position
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)
        return grid_x, grid_y

    def update_grid(self, grid, data):
        def mark_obstacle(grid, position, width, height, value=1, name="Unknown"):
            start_x, start_y = position
            end_x = start_x + width
            end_y = start_y + height

            for y in np.arange(start_y, end_y, self.grid_size):
                for x in np.arange(start_x, end_x, self.grid_size):
                    grid_x, grid_y = self.to_grid_coordinates((x, y))
                    if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
                        grid[grid_y][grid_x] = value

        grid.fill(0)

        # Mark all entities
        for entity_type, value in [
            ("registers", 5),  # Register
            ("shelves", 1),  # Shelf
            ("cartReturns", 6),  # Cart Return
            ("basketReturns", 7),  # Basket Return
            ("counters", 8),  # Counter
            ("carts", 2),  # Cart
            ("baskets", 3),  # Basket
        ]:
            for entity in data.get(entity_type, []):
                position = entity["position"]
                width, height = entity["width"], entity["height"]
                mark_obstacle(grid, position, width, height, value, name=entity_type)

        # Mark players explicitly with value 4
        for player in data.get("players", []):
            player_position = player["position"]
            player_width, player_height = self.player_width, self.player_height
            mark_obstacle(grid, player_position, player_width, player_height, value=4, name="player")

        logging.debug("Grid updated with new data.")

    def update_map(self, new_data):
        logging.debug("Updating map with new data.")
        self.data = new_data
        self.update_grid(self.grid, self.data)

    def is_obstacle(self, position):
        x, y = position

        for dx in np.arange(0, self.player_width, self.grid_size):
            for dy in np.arange(0, self.player_height, self.grid_size):
                grid_x = int((x + dx) / self.grid_size)
                grid_y = int((y + dy) / self.grid_size)

                if not (0 <= grid_y < self.rows and 0 <= grid_x < self.cols):
                    logging.warning(f"Position {position} is out of bounds and considered an obstacle.")
                    return True

                if self.grid[grid_y][grid_x] != 0:
                    logging.debug(f"Position {position} (adjusted for size) is an obstacle.")
                    return True
        return False

    def a_star_pathfinding(self, start, goal):
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance

        start = tuple(map(lambda x: int(x / self.grid_size), start))
        goal = tuple(map(lambda x: int(x / self.grid_size), goal))

        adjusted_goal = goal

        # Restrict approach to goal from north or south
        if self.is_obstacle((goal[0] * self.grid_size, goal[1] * self.grid_size)):
            logging.info("Goal is an obstacle. Searching for the closest open space north or south to the goal...")
            adjusted_goal = self.find_closest_north_south_open_space(goal)

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, adjusted_goal)}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == adjusted_goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()

                # Add the obstacle grid cell as the final step
                if adjusted_goal == goal or not self.is_obstacle((goal[0] * self.grid_size, goal[1] * self.grid_size)):
                    path.append(goal)
                logging.info(f"Path found: {path}")
                return [(x * self.grid_size, y * self.grid_size) for x, y in path]

            neighbors = [
                (current[0] + 1, current[1]),  # EAST
                (current[0] - 1, current[1]),  # WEST
                (current[0], current[1] - 1),  # NORTH
                (current[0], current[1] + 1),  # SOUTH
            ]

            for neighbor in neighbors:
                world_position = (neighbor[0] * self.grid_size, neighbor[1] * self.grid_size)

                if self.is_obstacle(world_position):
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, adjusted_goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        logging.error("No path found.")
        return None

    def find_closest_north_south_open_space(self, goal):
        """Find the closest open space north or south of the goal."""
        from collections import deque

        goal_x, goal_y = goal
        queue = deque([(goal_x, goal_y - 1), (goal_x, goal_y + 1)])  # NORTH and SOUTH neighbors
        visited = set(queue)

        while queue:
            current = queue.popleft()
            current_world_pos = (current[0] * self.grid_size, current[1] * self.grid_size)

            # Check if the current position is an open space
            if not self.is_obstacle(current_world_pos):
                logging.info(f"Closest open space (north/south) found: {current} for goal: {goal}.")
                return current

        logging.error(f"No open space found north or south of the goal: {goal}.")
        raise ValueError("No open space found north or south of the goal.")

    def print_map(self):
        # Mapping of values to single-character symbols and colors
        value_to_symbol = {
            0: (" ", "\033[0m"),  # Empty space (reset color)
            1: ("S", "\033[33m"),  # Shelf (Yellow)
            2: ("C", "\033[34m"),  # Cart (Blue)
            3: ("B", "\033[35m"),  # Basket (Magenta)
            4: ("P", "\033[32m"),  # Player (Green)
            5: ("R", "\033[31m"),  # Register (Red)
            6: ("T", "\033[36m"),  # Cart Return (Cyan)
            7: ("b", "\033[90m"),  # Basket Return (Gray)
            8: ("O", "\033[95m"),  # Counter (Purple)
        }

        logging.info("Grid Map:")
        for row in self.grid:
            row_output = []
            for cell in row:
                symbol, color = value_to_symbol.get(cell, ("?", "\033[91m"))  # Default to '?' in red for unknown values
                row_output.append(f"{color}{symbol}\033[0m")  # Add color and reset after each symbol
            logging.info("".join(row_output)) 