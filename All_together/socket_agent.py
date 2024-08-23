# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import json
import random
import socket

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

    while True:
        # action = str(random.randint(0, 1))
        # action += " " + random.choice(action_commands)  # random action

        # assume this is the only agent in the game
        i = 0
        while i < 20:
            action = "0 " + "SOUTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            output = json.loads(output)
            action = "1 " + "SOUTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            output = json.loads(output)
            i += 1

        i = 0
        while i < 20:
            action = "0 " + "NORTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            output = json.loads(output)
            action = "1 " + "NORTH"
            sock_game.send(str.encode(action))  # send action to env
            output = recv_socket_data(sock_game)  # get observation from env
            output = json.loads(output)
            i += 1

        print("Observations: ", output["observation"])
        print("Violations", output["violations"])
