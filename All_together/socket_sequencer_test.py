# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import json
import random
import socket
from sequencer import *
from pickup import *

from env import SupermarketEnv
from utils import recv_socket_data

if __name__ == "__main__":

    playerNumber = 0

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
    sock_game.send(str.encode(str(playerNumber) + " RESET"))  # reset the game
    output = recv_socket_data(sock_game)
    state = json.loads(output)
    shopping_list = state['observation']['players'][0]['shopping_list']
    position = state['observation']['players'][0]['position']
    starting_position = [3,17]
    target_list, reordered_shopping_list = sequenceInitialize(shopping_list, starting_position)
    print(reordered_shopping_list)
    print(target_list)
    PHASE = 2
    while True:
        if PHASE == 2:
            sock_game.send(str.encode(str(playerNumber) + " NOP"))  # reset the game
            output = recv_socket_data(sock_game)  # get observation from env
            state = json.loads(output)
            position = state['observation']['players'][playerNumber]['position']
            listOfTempObstacles = [state['observation']['players'][1]['position']]
            target_list, reordered_shopping_list = sequenceReorder(target_list, reordered_shopping_list, checkForReorder(position, target_list, listOfTempObstacles))
            print(reordered_shopping_list)
            print(target_list)

            if (abs(position[0] - target_list[0][0]) < 0.2 and abs(position[1] - target_list[0][1]) < 0.2):
                action_list = interacter(state, reordered_shopping_list)
                i = 0
                print("Reached here")
                while i < len(action_list[0]):
                    # print("Doing actions")
                    action = str(action_list[0][i])
                    # print("DOING THIS ACTION: "+str(action))
                    sock_game.send(str.encode(action))  # send action to env
                    output = recv_socket_data(sock_game)  # get observation from env
                    i += 1
            # break   
                reordered_shopping_list = reordered_shopping_list[1:]
                if len(target_list) == 1:
                    PHASE += 1
                target_list = target_list[1:]
                print("PICKED UP STUFF")
