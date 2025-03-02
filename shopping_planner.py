import logging
import json
import os
from itertools import permutations
from astar_agent import Agent, objs

SHOPPING_ORDER_FILE = "shopping_orders.json"
ITEM_LOCATIONS_FILE = "item_locations.json"
WINDOW_SIZE = 2

class ShoppingPlanner(Agent):
    def __init__(self, socket_game, env):
        super().__init__(socket_game, env)
        self.load_shopping_orders()
        self.load_item_locations()

    def load_shopping_orders(self):
        if os.path.exists(SHOPPING_ORDER_FILE):
            with open(SHOPPING_ORDER_FILE, "r") as f:
                self.shopping_orders = json.load(f)
                self.shopping_orders = {
                    tuple(sorted(k.split(","))): v for k, v in self.shopping_orders.items()
                }
            logging.info("Loaded cached shopping orders.")
        else:
            self.shopping_orders = {}

    def save_shopping_orders(self):
        json_compatible_orders = {
            ",".join(sorted(k)): v for k, v in self.shopping_orders.items()
        }
        with open(SHOPPING_ORDER_FILE, "w") as f:
            json.dump(json_compatible_orders, f, indent=4)
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
        return None

    def retrieve_order_from_chunks(self, shopping_list):
        chunks = self.get_order_chunks(shopping_list)
        possible_paths = []

        for perm in permutations(chunks):
            total_cost = 0
            retrieved_order = []
            used_items = set()
            valid_path = True

            for chunk in perm:
                sorted_chunk = tuple(sorted(chunk))
                if sorted_chunk in self.shopping_orders:
                    stored_data = self.shopping_orders[sorted_chunk]
                    if not isinstance(stored_data, dict) or "order" not in stored_data or "cost" not in stored_data:
                        continue
                    total_cost += stored_data["cost"]
                    for item in stored_data["order"]:
                        if item not in used_items:
                            retrieved_order.append(item)
                            used_items.add(item)
                else:
                    valid_path = False
                    break

            if valid_path:
                possible_paths.append((total_cost, retrieved_order))

        if not possible_paths:
            return None

        return min(possible_paths, key=lambda x: x[0])[1]

    def store_order_chunks(self, ordered_items, chunk_costs):
        for chunk, cost in chunk_costs.items():
            sorted_chunk = tuple(sorted(chunk))

            if sorted_chunk in self.shopping_orders:
                if cost < self.shopping_orders[sorted_chunk]["cost"]:
                    self.shopping_orders[sorted_chunk] = {"order": list(chunk), "cost": cost}
            else:
                self.shopping_orders[sorted_chunk] = {"order": list(chunk), "cost": cost}

        self.save_shopping_orders()

    def compute_shopping_order(self, shopping_list):
        retrieved_order = self.retrieve_order_from_chunks(shopping_list)

        if retrieved_order:
            logging.info(f"Using cached chunked order for: {shopping_list}")
            return [(item, self.get_item_position(item)) for item in retrieved_order]

        logging.info("\n--- COMPUTING OPTIMAL SHOPPING ROUTE ---\n")
        logging.info(f"Shopping List: {shopping_list}")

        basket_pos = [3.5, 16.5]
        shelf_positions = {item: self.get_item_position(item) for item in shopping_list if self.get_item_position(item)}

        current_position = basket_pos
        ordered_items = []
        chunk_costs = {}

        while shelf_positions:
            path_lengths = {
                item: (shelf, len(self.astar(current_position, shelf, objs, self.map_width, self.map_height)))
                for item, shelf in shelf_positions.items() if self.astar(current_position, shelf, objs, self.map_width, self.map_height)
            }

            if not path_lengths:
                logging.warning("No reachable shelves found! Adjusting shelf positions and current position.")

                adjusted_shelves = {}
                new_current_position = None

                for item, shelf in shelf_positions.items():
                    for offset in [0.25, -0.25, 0.5, -0.5, 1.0, -1.0]:
                        new_shelf = (shelf[0], shelf[1] + offset)
                        new_position = (current_position[0], current_position[1] + offset)
                        path = self.astar(new_position, new_shelf, objs, self.map_width, self.map_height)

                        if path:
                            adjusted_shelves[item] = new_shelf
                            self.item_locations[item] = list(new_shelf)
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

            best_item = min(path_lengths, key=lambda k: path_lengths[k][1])
            best_shelf = path_lengths[best_item][0]

            logging.info(f"Choosing Shelf at {best_shelf} (Path Length: {path_lengths[best_item][1]})")

            ordered_items.append(best_item)

            self.item_locations[best_item] = list(best_shelf)
            self.save_item_locations()

            new_position = (best_shelf[0], best_shelf[1] + 0.5)
            if not self.astar(current_position, new_position, objs, self.map_width, self.map_height):
                new_position = (best_shelf[0], best_shelf[1] - 0.5)

            chunk = (ordered_items[-2], best_item) if len(ordered_items) > 1 else None
            if chunk:
                cost = path_lengths[best_item][1]
                chunk_costs[chunk] = cost

            current_position = new_position
            shelf_positions[best_item] = new_position
            del shelf_positions[best_item]

        logging.info(f"\nFinal Optimized Shopping Order: {ordered_items}\n")

        self.store_order_chunks(ordered_items, chunk_costs)

        return [(item, self.get_item_position(item)) for item in ordered_items]
