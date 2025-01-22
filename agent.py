import json
import logging
from utils import recv_socket_data
from map import Map
from statemachine import StateMachine
from rrt import RRT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

direction_map = {0: "NORTH", 1: "SOUTH", 2: "EAST", 3: "WEST"}

def path_to_directions(path):
    directions = []
    for i in range(len(path) - 1):
        current = path[i]
        next_point = path[i + 1]
        delta_x = next_point[0] - current[0]
        delta_y = next_point[1] - current[1]

        if abs(delta_x) > abs(delta_y):  # Horizontal movement
            directions.append("EAST" if delta_x > 0 else "WEST")
        else:  # Vertical movement
            directions.append("NORTH" if delta_y < 0 else "SOUTH")
    return directions


class Agent:
    def __init__(self, sock_game, curr_player):
        self.sock_game = sock_game
        self.curr_player = curr_player
        self.map = None
        self.state_machine = StateMachine(self)
        self.last_violation = ""

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
        else:
            self.last_violation = ""
        return self.curr_state

    def has_basket(self):
        return len(self.curr_state["baskets"] )!= 0

    def shopping_list(self):
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
        rrt = RRT(self.map, player_position, target_position)
        path = rrt.plan()

        logging.info(f"Moving from {player_position} to {target} at {target_position}")

        if not path:
            logging.error(f"Failed to find a path to {target} using RRT.")
            return False

        directions = path_to_directions(path)
        logging.info(f"Movement directions: {directions}")

        for direction in directions:
            # self.map.print_map(target_position)
            self.send_action(direction)
            if self.check_reached_location(target):
                return True
            if self.check_collision():
                logging.warning("Collision detected. Replanning...")
                return self.move_to(target, target_position)  # Replan dynamically

        return True
    
    def interact(self):
        self.send_action("INTERACT")

    def item_in_hand(self, item):
        return self.get_self()["holding_food"] == item

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
