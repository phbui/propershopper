import logging
import json
import os
import itertools
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

    def get_order_chunks(self, shopping_list):
        return [tuple(sorted(shopping_list[i:i + WINDOW_SIZE])) for i in range(len(shopping_list) - WINDOW_SIZE + 1)]

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

        distance_matrix = {}
        stored_chunk_costs = {tuple(sorted(chunk)): data["cost"] for chunk, data in self.shopping_orders.items() if isinstance(data, dict) and "cost" in data}

        for item1, item2 in itertools.combinations(shelf_positions.keys(), 2):
            sorted_chunk = tuple(sorted((item1, item2)))
            
            if sorted_chunk in stored_chunk_costs:
                distance_matrix[(item1, item2)] = stored_chunk_costs[sorted_chunk]
                distance_matrix[(item2, item1)] = stored_chunk_costs[sorted_chunk]
            else:
                pos1, pos2 = shelf_positions[item1], shelf_positions[item2]
                path = self.astar(pos1, pos2, objs, self.map_width, self.map_height)
                if path:
                    distance_matrix[(item1, item2)] = len(path)
                    distance_matrix[(item2, item1)] = len(path)
                else:
                    distance_matrix[(item1, item2)] = float('inf')
                    distance_matrix[(item2, item1)] = float('inf')

        ordered_items = []
        unvisited = set(shelf_positions.keys())
        current_position = basket_pos

        while unvisited:
            def get_path_length(item):
                path = self.astar(current_position, shelf_positions[item], objs, self.map_width, self.map_height)
                return len(path) if path else float('inf')

            next_item = min(unvisited, key=get_path_length, default=None)

            if next_item is None or get_path_length(next_item) == float('inf'):
                logging.warning("No reachable items found! Attempting node nudging.")

                adjusted_shelves = {}
                new_current_position = None

                for item in unvisited:
                    shelf = shelf_positions[item]
                    for offset in [0.25, -0.25, 0.5, -0.5, 1.0, -1.0]:
                        new_shelf = (shelf[0], shelf[1] + offset)
                        new_position = (current_position[0], current_position[1] + offset)
                        path = self.astar(new_position, new_shelf, objs, self.map_width, self.map_height)

                        if path:
                            adjusted_shelves[item] = new_shelf
                            self.item_locations[item] = list(new_shelf)
                            self.save_item_locations()
                            if not new_current_position:
                                new_current_position = new_position
                            break
                    else:
                        logging.warning(f"Still no path to shelf for {item}. Skipping.")

                if not adjusted_shelves:
                    logging.error("Even with adjustments, no valid shelf positions found. Stopping shopping route.")
                    break

                shelf_positions.update(adjusted_shelves)
                if new_current_position:
                    current_position = new_current_position
                continue

            ordered_items.append(next_item)
            current_position = shelf_positions[next_item]
            unvisited.remove(next_item)

        chunk_costs = {}
        for i in range(len(ordered_items) - 1):
            chunk = tuple(sorted((ordered_items[i], ordered_items[i + 1])))
            cost = distance_matrix.get((ordered_items[i], ordered_items[i + 1]), float('inf'))
            chunk_costs[chunk] = cost

        logging.info(f"\nFinal Optimized Shopping Order: {ordered_items}\n")

        self.store_order_chunks(ordered_items, chunk_costs)

        return [(item, self.get_item_position(item)) for item in ordered_items]
