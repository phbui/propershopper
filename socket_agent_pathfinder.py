import sys
import json
import socket
import logging
from utils import recv_socket_data
from shopping_planner import ShoppingPlanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    while True:
        action = "0 " + "NOP"

        print("Sending action: ", action)
        sock_game.send(str.encode(action))  # send action to env

        output = recv_socket_data(sock_game)  # get observation from env
        output = json.loads(output)

        shopping_planner = ShoppingPlanner(sock_game, output)
        ordered_shelves = shopping_planner.compute_shopping_order(output['observation']['players'][0]['shopping_list'][:6])