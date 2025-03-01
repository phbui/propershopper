from astar_path_planner_0 import Agent

class ShoppingPlanner(Agent):
    def __init__(self, socket_game, env):
        super().__init__(socket_game, env)  # Initialize from Agent class

    def compute_shopping_order(self, shopping_list):
        shelf_positions = []
        for item in shopping_list:
            for shelf in self.obs['shelves']:
                if shelf['food_name'] == item:
                    shelf_positions.append(shelf['position'])
                    break  # Ensure no duplicate entries

        # Start from player's position
        current_position = tuple(self.player['position'])

        # Use A* to determine the best visiting order
        ordered_shelves = []
        while shelf_positions:
            # Find the closest shelf using A*
            best_shelf = min(shelf_positions, key=lambda s: len(self.astar(current_position, s, self.obs['shelves'], self.map_width, self.map_height)))
            ordered_shelves.append(best_shelf)
            current_position = best_shelf
            shelf_positions.remove(best_shelf)

        return ordered_shelves
