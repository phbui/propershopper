# Author: Gyan Tatiya
# Email: Gyan.Tatiya@tufts.edu

import socket
from agent_astar import Agent_AStar
from agent_qlearn import Agent_QLearn

if __name__ == "__main__":

    # Make the env
    # env_id = 'Supermarket-v0'
    # env = gym.make(env_id)

    # Connect to Supermarket
    HOST = '127.0.0.1'
    PORT = 9000
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect((HOST, PORT))

    # agent_astar = Agent_AStar(sock_game, 0)
    # agent_astar.send_action("NOP")
    # agent_astar.run()

    print("Starting Agent_QLearning")
    agent_qlearn = Agent_QLearn(sock_game, 0)
    agent_qlearn.run()

