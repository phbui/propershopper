import numpy as np  # type: ignore
import heapq
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Map:
    def __init__(self, data, grid_size=0.15, player_size=(0.6, 0.4)):
        self.grid_size = grid_size
        self.data = data
        self.player_width, self.player_height = player_size
        self.grid = self.construct_map()
        self.rows, self.cols = self.grid.shape
        logging.debug("Map initialized.")
        self.print_map()

    def construct_map(self):
        all_positions = []
        for entity_type in ["registers", "shelves", "cartReturns", "basketReturns", "counters", "carts"]:
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
            # Calculate buffered boundaries
            buffer_x = 0.5 * self.grid_size # Ensure buffer scales with grid size
            buffer_y = 1 * self.grid_size
            start_x = max(0, position[0] - buffer_x)
            start_y = max(0, position[1] - buffer_y)
            end_x = min(position[0] + width + buffer_x, self.cols * self.grid_size)
            end_y = min(position[1] + height + buffer_y, self.rows * self.grid_size)

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
        ]:
            for entity in data.get(entity_type, []):
                position = entity["position"]
                width, height = entity["width"], entity["height"]
                mark_obstacle(grid, position, width, height, value, name=entity_type)

        # Mark players explicitly with value 4
        #for player in data.get("players", []):
        #    player_position = player["position"]
        #    player_width, player_height = self.player_width, self.player_height
        #   mark_obstacle(grid, player_position, player_width, player_height, value=4, name="player")

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

    def print_map(self, goal=None):
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

        print(f"goal at: {goal}")

        logging.info("Grid Map:")
        for row_index, row in enumerate(self.grid):
            row_output = []
            for col_index, cell in enumerate(row):
                if goal:

                    goal_x, goal_y = self.to_grid_coordinates(goal)
                    if (col_index, row_index) == (goal_x, goal_y):  # Inverted y-axis
                        row_output.append(f"\033[91mG\033[0m")  # Highlight goal as 'G' in red
                        continue
                symbol, color = value_to_symbol.get(cell, ("?", "\033[91m"))  # Default to '?' in red for unknown values
                row_output.append(f"{color}{symbol}\033[0m")  # Add color and reset after each symbol
            logging.info("".join(row_output)) 