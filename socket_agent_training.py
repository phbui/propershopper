#Author Hang Yu

import json
import random
import socket
import numpy as np

import gymnasium as gym
from env import SupermarketEnv
from utils import recv_socket_data

from Q_Learning_agent import QLAgent  # Make sure to import your QLAgent class
import pickle
import pandas as pd

from shopping_planner import ShoppingPlanner

cart = False
exit_pos = [-0.8, 15.6] # The position of the exit in the environment from [-0.8, 15.6] in x, and y = 15.6
cart_pos_left = [1, 18.5] # The position of the cart in the environment from [1, 2] in x, and y = 18.5
cart_pos_right = [2, 18.5] 

def distance_to_cart(state):
    agent_position = state['observation']['players'][0]['position']
    if agent_position[0] > 1.5:
        cart_distances = [euclidean_distance(agent_position, cart_pos_right)]
    else:
        cart_distances = [euclidean_distance(agent_position, cart_pos_left)]
    return min(cart_distances)

def euclidean_distance(pos1, pos2):
    # Calculate Euclidean distance between two points
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5


def calculate_reward(previous_state, current_state):
    reward = 0
    agent_pos = current_state['observation']['players'][0]['position']
    prev_pos = previous_state['observation']['players'][0]['position']
    shopping_list = current_state['observation']['players'][0]['shopping_list']
    holding_food = current_state['observation']['players'][0]['holding_food']
    bagged_items = current_state['observation']['players'][0]['bagged_items']
    violations = current_state.get('violations', "")

    exit_pos = [-0.8, 15.6]  # Store exit position

    # Encourage movement toward the correct shelf
    def get_shelf_position(item_name):
        for shelf in current_state['observation']['shelves']:
            if shelf['food_name'] == item_name:
                return shelf['position']
        return None

    if shopping_list:
        target_item = shopping_list[0]  # Prioritize the first item in the list
        target_pos = get_shelf_position(target_item)

        if target_pos:
            prev_dist = np.linalg.norm(np.array(prev_pos) - np.array(target_pos))
            curr_dist = np.linalg.norm(np.array(agent_pos) - np.array(target_pos))

            if curr_dist < prev_dist:
                reward += 5  # Moving closer
            if curr_dist < 0.6:
                reward += 10  # Reached the shelf

    # Reward for picking up the correct item
    if holding_food and holding_food in shopping_list:
        reward += 10
    elif holding_food and holding_food not in shopping_list:
        reward -= 5  # Picking up the wrong item

    # Reward for placing items in the basket
    if len(bagged_items) > len(previous_state['observation']['players'][0]['bagged_items']):
        reward += 15

    # 🚨 Penalize norm violations
    if "PersonalSpaceNorm" in violations:
        reward -= 10
    if "BlockingShelfNorm" in violations:
        reward -= 10
    if "WallCollisionViolation" in violations:
        reward -= 15  # Hitting a wall is a major mistake
    if "PlayerCollisionNorm" in violations:
        reward -= 20  # Bumping into another player
    if "ObjectCollisionNorm" in violations:
        reward -= 10  # Hitting an object (e.g., shelves, registers)

    exit_distance = np.linalg.norm(np.array(agent_pos) - np.array(exit_pos))
    if exit_distance < 2.0:  # If within 2 units of the exit, penalize
        reward -= 10
    elif exit_distance < 4.0:  # Lesser penalty if within 4 units
        reward -= 5

    # Penalize unnecessary movement
    if agent_pos == prev_pos:
        reward -= 1  # No movement penalty

    return reward

if __name__ == "__main__":
    action_commands = ['NOP', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'TOGGLE_CART', 'INTERACT', 'RESET']
    
    agent = QLAgent(action_space=len(action_commands) - 1)  
    sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_game.connect(('127.0.0.1', 9000))

    training_time = 100
    episode_length = 1000

    for episode in range(training_time):
        sock_game.send(str.encode("0 RESET"))  # Reset the game
        state = recv_socket_data(sock_game)
        state = json.loads(state)
        agent_pos = state['observation']['players'][0]['position']
        shopping_list = state['observation']['players'][0]['shopping_list']
        # Create the planner
        shopping_planner = ShoppingPlanner(socket_game=sock_game, env=state)

        # Compute the optimal shopping order using A*
        ordered_shelves = shopping_planner.compute_shopping_order(shopping_list)

        for shelf_pos in ordered_shelves:
            # Use Q-learning to navigate to each shelf
            cnt = 0
            while not state['gameOver'] and cnt < episode_length:
                cnt += 1
                action_index = agent.choose_action(state, subtask="navigate_shelf")
                action = "0 " + action_commands[action_index]

                sock_game.send(str.encode(action))
                next_state = recv_socket_data(sock_game)
                next_state = json.loads(next_state)

                reward = calculate_reward(state, next_state)
                agent.learning(action_index, reward, state, next_state, subtask="navigate_shelf")

                state = next_state
                agent.qtable_navigate_shelf.to_json('qtable_shelf.json')


        for shelf_pos in ordered_shelves:
            cnt = 0
            while not state['gameOver'] and cnt < episode_length:
                cnt += 1
                action_index = agent.choose_action(state, subtask="navigate_shelf")
                action = "0 " + action_commands[action_index]

                sock_game.send(str.encode(action))
                next_state = recv_socket_data(sock_game)
                next_state = json.loads(next_state)

                reward = calculate_reward(state, next_state)
                agent.learning(action_index, reward, state, next_state, subtask="navigate_shelf")

                state = next_state
                agent.qtable_navigate_shelf.to_json('qtable_shelf.json')

            # Once at the shelf, use Q-learning to pick the item
            action_index = agent.choose_action(state, subtask="pick_place")
            sock_game.send(str.encode("0 INTERACT"))  # Pick the item
            next_state = recv_socket_data(sock_game)
            next_state = json.loads(next_state)
            reward = calculate_reward(state, next_state)
            agent.learning(action_index, reward, state, next_state, subtask="pick_place")

        # Navigate to checkout after finishing shopping
        path_to_register = agent.astar(agent_pos, [2, 4.5], state['observation']['shelves'], 20, 25)
        if path_to_register:
            for step in path_to_register:
                sock_game.send(str.encode("0 " + step))  # Move step by step

        sock_game.send(str.encode("0 INTERACT"))  # Checkout

    sock_game.close()

