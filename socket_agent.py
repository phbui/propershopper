# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import json
import random
import socket

from env import SupermarketEnv
from utils import recv_socket_data

def navigate_json(json_obj, keys):
    current = json_obj
    for key in keys:
        current = current[key]
    return current

class Quest:
    def __init__(self, name):
        self.name = name
        self.requirements = []
        print(f"Created [Quest: {self.name}].")

    def __init__(self, name, requirements):
        self.name = name
        self.requirements = requirements
        print(f"Created [Quest: {self.name}].")

    def set_requirements(self, requirements):
        self.requirements = requirements

    def add_requirements(self, key, quantity):
        if key in self.requirements:
            print(f"[Quest: {self.name}] Requirement '{key}' already exists with quantity {self.requirements[key]}.")
        else:
            self.requirements[key] = quantity
            print(f"[Quest: {self.name}] Added requirement '{key}' with quantity {quantity}.")
            
    def modify_requirements(self, key, quantity):
        if key in self.requirements:
            self.requirements[key] = quantity
            print(f"[Quest: {self.name}] Modified requirement '{key}' to new quantity {quantity}.")
        else:
            print(f"[Quest: {self.name}] Requirement '{key}' does not exist.")

    def remove_requirements(self, key):
        if key in self.requirements:
            del self.requirements[key]
            print(f"[Quest: {self.name}] Removed requirement '{key}'.")
        else:
            print(f"[Quest: {self.name}] Requirement '{key}' does not exist.")


class Agent:
    def __init__(self, socket, curr_player):
        self.socket = socket
        self.curr_player = curr_player

    def send_action(self, action):
        action = str(self.curr_player) + " " + action
        print("Sending action: ", action)
        sock_game.send(str.encode(action))  # send action to env

        output = recv_socket_data(sock_game)  # get observation from env
        self.current_state = json.loads(output)
        return self.current_state

    def turn_to(self, target):
        # target is in the form of an array of keys in json
        player_direction = self.current_state["direction"]
        target_direction = navigate_json(self.current_state, [target])["direction"]

        if (player_direction != target_direction):
            print()

    def move_to(self, target):
        # target is in the form of an array of keys in json

        player_position = self.current_state["position"]
        target_position = navigate_json(self.current_state, [target])["position"]

        while player_position != target_position:
            delta_x = target_position[0] - player_position[0]
            delta_y = target_position[1] - player_position[1]

            # Determine the next action
            if abs(delta_x) > abs(delta_y):  # Move horizontally
                if delta_x > 0:
                    action = "EAST"
                else:
                    action = "WEST"
            else:  # Move vertically
                if delta_y > 0:
                    action = "NORTH"
                else:
                    action = "SOUTH"

            # Send the action to the environment
            print(f"Moving from {player_position} towards {target_position} using action {action}")
            self.current_state = self.send_action(action)

            # Update the player's current position
            player_position = self.current_state["position"]

        print(f"Arrived at target position: {target_position}")

    def check_carts():
        print()

    def get_cart():
        print()

    def load_cart():
        print()

    def check_inventory():
        print()

    def retrieve_item():
        print()

    def find_item():
        print()

    def check_out():
        print

    def check_quest_requirements():
        print()

    def check_hand():  
        print()
    
    def complete_quest(self, quest):
        print()
    


if __name__ == "__main__":

    # Make the env
    # env_id = 'Supermarket-v0'
    # env = gym.make(env_id)

    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT']

    print("action_commands: ", action_commands)

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    agent = Agent(socket, 0)

    quest = Quest("HW0", [{"any": 2}])

    agent.send_action("NOP")
    agent.complete_quest(quest)