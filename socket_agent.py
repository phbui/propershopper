# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import socket
from quest import Quest
from agent import Agent

from env import SupermarketEnv
from utils import recv_socket_data


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

    agent = Agent(sock_game, 0)

    quest = Quest("HW0", [{"any": 2}])

    agent.send_action("NOP")
    agent.complete_quest(quest)