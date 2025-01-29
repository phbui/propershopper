import json
import logging
from utils import recv_socket_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Agent_Class:
    DIRECTION_MAP = {0: "NORTH", 1: "SOUTH", 2: "EAST", 3: "WEST"}
    ACTION_COMMANDS = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']

    def __init__(self, sock_game, curr_player):
        self.sock_game = sock_game
        self.curr_player = curr_player

    def send_action(self, action):
        action = f"{self.curr_player} {action}"
        logging.debug(f"Sending action: {action}")
        self.sock_game.send(str.encode(action))
        output = recv_socket_data(self.sock_game)
        output_json = json.loads(output)
        return output_json