import json
import logging
from utils import recv_socket_data
from map import Map
from statemachine import StateMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

direction_map = {0: "NORTH", 1: "SOUTH", 2: "EAST", 3: "WEST"}

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
                    y = y + entity["height"] / 2 - 0.25

                    return x, y
        logging.error(f"Item '{item}' not found in shelves or counters.")
        return None

    def get_exit_position(self):
        return self.curr_state["exit"]["position"]
    
    def check_direction(self, target_direction):
        if self.get_self()['direction'] != target_direction:
            self.send_action(target_direction)

    def calculate_direction(self, current, target):
        current_x, current_y = current
        target_x, target_y = target

        # Determine direction
        if target_y > current_y:
            return direction_map[1]  # NORTH
        elif target_y < current_y:
            return direction_map[3]  # SOUTH
        elif target_x > current_x:
            return direction_map[2]  # EAST
        elif target_x < current_x:
            return direction_map[4]  # WEST
        else:
            return None

    def move_to(self, target, target_position):
        player_position = tuple(self.get_self()["position"])
        target_position = tuple(target_position)
        
        path = self.map.a_star_pathfinding(player_position, target_position)

        if not path:
            #logging.error(f"No path to {target} found!")
            return False
        
        previous_positions = []
        repeat_count = 0  # Counter for detecting repeated movement
        max_repeats = 2  # Threshold for switching axis

        for i, waypoint in enumerate(path):
            is_last_waypoint = (i == len(path) - 1)
            while True:
                self.map.print_map(target_position)
                player_position = tuple(self.get_self()["position"])
                logging.info(f"Moving from {player_position} to {target} through waypoint: {waypoint}.")
                delta_x, delta_y = waypoint[0] - player_position[0], waypoint[1] - player_position[1]
                if is_last_waypoint and abs(delta_x) < 0.5 and abs(delta_y) < 0.5:
                    logging.info(f"Reached final target: {target_position}.")
                    self.check_direction(self.calculate_direction(player_position, target_position))
                    return True
                elif not is_last_waypoint and abs(delta_x) < 0.5 and abs(delta_y) < 0.5:
                    break
                if self.check_reached_location(target):
                    self.check_direction(self.calculate_direction(player_position, target_position))
                    return True
                
                # Detect repeated movements
                if previous_positions and player_position == previous_positions[-1]:
                    repeat_count += 1
                    logging.warning(f"Repeated position detected: {player_position}. Repeat count: {repeat_count}")
                else:
                    repeat_count = 0  # Reset repeat count if movement progresses
                previous_positions.append(player_position)

                if repeat_count >= max_repeats:
                    # Switch axis if stuck
                    if abs(delta_x) >= abs(delta_y):  # Previously moving in x-axis
                        action = "NORTH" if delta_y < 0 else "SOUTH"
                    else:  # Previously moving in y-axis
                        action = "EAST" if delta_x > 0 else "WEST"
                    logging.warning(f"Switching axis due to repeated movement. New action: {action}")
                else:
                    # Normal movement logic
                    if abs(delta_x) >= abs(delta_y):
                        action = "EAST" if delta_x > 0 else "WEST"
                    else:
                        action = "NORTH" if delta_y < 0 else "SOUTH"

                self.send_action(action)
        return False

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

    def run(self):
        while self.state_machine.state != "Leave":
            self.state_machine.handle_state()
