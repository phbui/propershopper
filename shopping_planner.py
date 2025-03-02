import logging
import json
import os
from astar_agent import Agent, objs

SHOPPING_ORDER_FILE = "shopping_orders.json"
ITEM_LOCATIONS_FILE = "item_locations.json"

class ShoppingPlanner(Agent):
    def __init__(self, socket_game, env):
        super().__init__(socket_game, env)
        self.load_shopping_orders()
        self.load_item_locations()

    def load_shopping_orders(self):
        if os.path.exists(SHOPPING_ORDER_FILE):
            with open(SHOPPING_ORDER_FILE, "r") as f:
                self.shopping_orders = json.load(f)
            logging.info("Loaded cached shopping orders.")
        else:
            self.shopping_orders = {}

    def save_shopping_orders(self):
        with open(SHOPPING_ORDER_FILE, "w") as f:
            json.dump(self.shopping_orders, f, indent=4)
        logging.info("Saved updated shopping orders.")

    def load_item_locations(self):
        if os.path.exists(ITEM_LOCATIONS_FILE):
            with open(ITEM_LOCATIONS_FILE, "r") as f:
                self.item_locations = json.load(f)
            logging.info("Loaded cached item locations.")
        else:
            self.item_locations = {}

    def save_item_locations(self):
        with open(ITEM_LOCATIONS_FILE, "w") as f:
            json.dump(self.item_locations, f, indent=4)
        logging.info("Saved updated item locations.")

    def get_item_position(self, item):
        if item in self.item_locations:
            return tuple(self.item_locations[item])

        # Fallback: Search shelves and counters
        for shelf in self.obs['shelves']:
            if shelf['food_name'] == item:
                pos = [shelf['position'][0] + 1, shelf['position'][1]]
                self.item_locations[item] = pos
                self.save_item_locations()
                return tuple(pos)

        for counter in self.obs['counters']:
            if counter['food'] == item:
                self.item_locations[item] = counter['position']
                self.save_item_locations()
                return tuple(counter['position'])

        logging.warning(f"Item '{item}' not found in shelves or counters!")
        return None  # Indicate item wasn't found

    def compute_shopping_order(self, shopping_list):
        order_key = self.get_order_key(shopping_list)

        if order_key in self.shopping_orders:
            logging.info(f"Using cached shopping order for: {shopping_list}")
            return self.shopping_orders[order_key]

        logging.info("\n--- COMPUTING OPTIMAL SHOPPING ROUTE ---\n")
        logging.info(f"Shopping List: {shopping_list}")

        basket_pos = [3.5, 16.5]
        shelf_positions = {}

        for item in shopping_list:
            position = self.get_item_position(item)
            if position:
                shelf_positions[item] = position

        current_position = basket_pos
        ordered_shelves = []
        
        while shelf_positions:
            path_lengths = {}

            for item, shelf in shelf_positions.items():
                path = self.astar(current_position, shelf, objs, self.map_width, self.map_height)
                if path:
                    path_lengths[item] = (shelf, len(path))

            if not path_lengths:
                logging.warning("No reachable shelves found! Adjusting shelf positions and current position.")

                # Try modifying shelf positions and also shifting `current_position`
                adjusted_shelves = {}
                new_current_position = None

                for item, shelf in shelf_positions.items():
                    for offset in [0.25, -0.25, 0.5, -0.5, 1.0, -1.0]:
                        new_shelf = (shelf[0], shelf[1] + offset)
                        new_position = (current_position[0], current_position[1] + offset)
                        path = self.astar(new_position, new_shelf, objs, self.map_width, self.map_height)

                        if path:
                            adjusted_shelves[item] = new_shelf
                            self.item_locations[item] = list(new_shelf)  # **Store nudge result**
                            if not new_current_position:
                                new_current_position = new_position
                            break
                    else:
                        logging.warning(f"Still no path to shelf for {item}. Skipping.")

                if not adjusted_shelves:
                    logging.error("Even with adjustments, no valid shelf positions found. Stopping shopping route.")
                    break

                shelf_positions = adjusted_shelves
                if new_current_position:
                    current_position = new_current_position
                continue

            # Select the best shelf based on shortest path
            best_item = min(path_lengths, key=lambda k: path_lengths[k][1])
            best_shelf = path_lengths[best_item][0]

            logging.info(f"Choosing Shelf at {best_shelf} (Path Length: {path_lengths[best_item][1]})")

            # Store as tuple (item_name, shelf_position)
            ordered_shelves.append((best_item, best_shelf))

            # **Store the nudged position permanently**
            self.item_locations[best_item] = list(best_shelf)
            self.save_item_locations()

            # Shift both `current_position` and `shelf_position`
            new_position = (best_shelf[0], best_shelf[1] + 0.5)
            if not self.astar(current_position, new_position, objs, self.map_width, self.map_height):
                new_position = (best_shelf[0], best_shelf[1] - 0.5)

            current_position = new_position
            shelf_positions[best_item] = new_position
            del shelf_positions[best_item]

        logging.info(f"\nFinal Optimized Shopping Route: {ordered_shelves}\n")

        self.shopping_orders[order_key] = ordered_shelves
        self.save_shopping_orders()

        return ordered_shelves
