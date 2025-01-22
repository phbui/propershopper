import json
import math
import logging
from utils import recv_socket_data
from map import Map
from astar import AStar
from statemachine import StateMachine


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

direction_map = {0: "NORTH", 1: "SOUTH", 2: "EAST", 3: "WEST"}

import math

def path_to_directions(path, step_size=0.15):
    directions = []

    for i in range(len(path) - 1):
        current = path[i]
        next_point = path[i + 1]
        dx = next_point[0] - current[0]
        dy = next_point[1] - current[1]

        # Determine whether we move horizontally or vertically
        # (assuming no diagonal steps).
        if abs(dx) > abs(dy):
            # Horizontal movement
            distance = abs(dx)
            move_dir = "EAST" if dx > 0 else "WEST"
        else:
            # Vertical movement
            distance = abs(dy)
            move_dir = "NORTH" if dy < 0 else "SOUTH"

        # Number of 0.15-unit steps needed
        steps_needed = int(math.ceil(distance / step_size))

        if directions and (move_dir != directions[-1]):
            directions.append(move_dir)  # "turn" in the new direction

        # Add the actual steps
        for _ in range(steps_needed):
            directions.append(move_dir)

    return directions

class Agent:
    def __init__(self, sock_game, curr_player, shopping_list=None):
        self.sock_game = sock_game
        self.curr_player = curr_player
        self.map = None
        self.state_machine = StateMachine(self)
        self.last_violation = ""
        self.shopping_list = shopping_list

    def send_action(self, action):
        action = f"{self.curr_player} {action}"
        logging.debug(f"Sending action: {action}")
        self.sock_game.send(str.encode(action))
        output = recv_socket_data(self.sock_game)
        output_json = json.loads(output)
        self.curr_state = output_json["observation"]
        if not self.map:
            self.map = Map(self.curr_state)
        else:
            self.map.update_map(self.curr_state)

        if output_json["violations"]:
            self.last_violation = output_json["violations"][0]
            logging.warning(f"Violation: {self.last_violation}")
        return self.curr_state
    
    def correct_direction(self, target):
        player_x, player_y = self.get_self()["position"]
        target_x, target_y = target

        direction = "NOP"

        # Determine direction
        if target_y < player_y:
            direction = direction_map[0]  # NORTH
        elif target_y > player_y:
            direction = direction_map[1]  # SOUTH
        elif target_x > player_x:
            direction = direction_map[2]  # EAST
        elif target_x < player_x:
            direction = direction_map[3]  # WEST

        self.send_action(direction)

    def has_basket(self):
        return len(self.curr_state["baskets"] )!= 0

    def get_shopping_list(self):
        if self.shopping_list is not None:
            return self.shopping_list
        else:
            return self.get_self()["shopping_list"]

    def basket_return_position(self):
        return self.curr_state["basketReturns"][0]["position"]

    def get_item_location(self, item):
        for entity_type in ["shelves", "counters"]:
            for entity in self.curr_state.get(entity_type, []):
                if entity["food"] == item:
                    logging.info(f"Item '{item}' found in {entity_type} at position {entity['position']}.")
                    x, y = entity["position"]
                    x = x + entity["width"] / 2
                    y = y + entity["height"]

                    return x, y
        logging.error(f"Item '{item}' not found in shelves or counters.")
        return None

    def get_exit_position(self):
        return self.curr_state["exit"]["position"]
    
    def check_direction(self, target_direction):
        if self.get_self()['direction'] != target_direction:
            self.send_action(target_direction)

    def move_to(self, target, target_position):
        player_position = tuple(self.get_self()["position"])
        astar = AStar(self.map, player_position, target_position)
        path = astar.plan()

        logging.info(f"Moving from {player_position} to {target} at {target_position}")

        if not path:
            logging.error(f"Failed to find a path to {target} using A*.")
            return False

        directions = path_to_directions(path)
        logging.info(f"Movement directions: {directions}")

        if self.check_reached_location(target):
            return True
    

        for direction in directions:
            self.send_action(direction)

            if self.check_reached_location(target):
                return True
            if self.check_collision():
                logging.warning("Collision detected. Replanning...")
                return self.move_to(target, target_position)  # Re-run if needed
        
        self.correct_direction(target_position)

    def interact(self):
        self.send_action("INTERACT")

    def item_in_hand(self, item):
        return self.get_self()["holding_food"] == item
    
    def get_nearest_cart(self):
        player_position = self.get_self()["position"]
        carts = self.curr_state["carts"]

        if not carts:
            return -1

        nearest_cart_index = min(
            range(len(carts)),
            key=lambda i: self._calculate_distance(player_position, carts[i]["position"])
        )
        return nearest_cart_index

    def get_nearest_basket(self):
        player_position = self.get_self()["position"]
        baskets = self.curr_state["baskets"]

        if not baskets:
            return -1

        nearest_basket_index = min(
            range(len(baskets)),
            key=lambda i: self._calculate_distance(player_position, baskets[i]["position"])
        )

        return nearest_basket_index

    def _calculate_distance(self, position1, position2):
        return math.sqrt(
            (position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2
        )
    
    def item_in_cart(self, item):
        nearest_cart_index = self.get_nearest_cart()
        if nearest_cart_index != -1:
            return item in self.curr_state["carts"][self.get_nearest_cart()]["contents"]
        else:
            return False
    
    def item_in_basket(self, item):
        nearest_basket_index = self.get_nearest_basket()
        if nearest_basket_index != -1:
            return item in self.curr_state["baskets"][nearest_basket_index]["contents"]
        return False

    def check_reached_location(self, keyword):
        return keyword.lower() in self.last_violation.lower()
    
    def check_collision(self):
        return "ran into".lower() in self.last_violation.lower()

    def get_self(self):
        return self.curr_state["players"][self.curr_player]
    
    def get_exit_position(self):
        return [0, 15.3]


    def run(self):
        while self.state_machine.state != "Leave":
            self.state_machine.handle_state()
