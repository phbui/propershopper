import json
import socket
import numpy as np
import pandas as pd
import logging
import sys

from env import SupermarketEnv
from utils import recv_socket_data
from Q_Learning_agent import QLAgent
from shopping_planner import ShoppingPlanner

basket_pos = [3.5, 18.5]
exit_pos = [-0.8, 15.6]
cart_pos_left = [1, 18.5]
cart_pos_right = [2, 18.5]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class SupermarketTrainer:
    def __init__(self, host='127.0.0.1', port=9000, episodes=100):
        self.action_commands = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'INTERACT']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.agent = QLAgent(action_space=len(self.action_commands) - 1)
        self.episodes = episodes

    def distance(self, a, b):
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def calculate_reward(self, state, prev_state, subtask, target_item=None):
        agent_pos = state['observation']['players'][0]['position']
        prev_pos = prev_state['observation']['players'][0]['position']
        holding_food = state['observation']['players'][0]['holding_food']
        baskets = state['observation']['baskets']
        prev_baskets = prev_state['observation']['baskets']
        carts = state['observation']['carts']
        violations = state.get('violations', "")

        has_basket = len(baskets) > 0 and baskets[0]['owner'] == 0
        prev_basket_contents = prev_baskets[0]['contents'] if len(prev_baskets) > 0 else []
        current_basket_contents = baskets[0]['contents'] if has_basket else []

        # Compute penalties
        penalties = self.compute_penalties(agent_pos, carts, violations)

        # Apply appropriate subtask reward calculation
        if subtask == "navigate_basket":
            return self.reward_navigate_basket(agent_pos, prev_pos, basket_pos, has_basket, prev_baskets, penalties, "Navigate Basket")

        if subtask == "pick_basket":
            return self.reward_pick_basket(agent_pos, prev_pos, has_basket, prev_baskets, penalties)

        if subtask == "navigate_shelf" and target_item:
            return self.reward_navigate_shelf(state, prev_pos, agent_pos, target_item, penalties)

        if subtask == "pick_place" and target_item:
            return self.reward_pick_place(agent_pos, prev_pos, holding_food, target_item, current_basket_contents, prev_basket_contents, penalties)

        return penalties["norm"] + penalties["exit"] + penalties["cart"]


    def compute_penalties(self, agent_pos, carts, violations):
        exit_distance = self.distance(agent_pos, exit_pos)
        exit_penalty = -10 if exit_distance < 2.0 else -5 if exit_distance < 4.0 else 0

        cart_penalty = sum([-10 if self.distance(agent_pos, cart['position']) < 1.5 else 0 for cart in carts])

        norm_penalty = sum([
            -10 if "BlockingShelfNorm" in violations else 0,
            -15 if "WallCollisionViolation" in violations else 0,
            -20 if "PlayerCollisionNorm" in violations else 0,
            -10 if "ObjectCollisionNorm" in violations else 0
        ])

        return {"norm": norm_penalty, "exit": exit_penalty, "cart": cart_penalty}


    def reward_navigate_basket(self, agent_pos, prev_pos, target_pos, success_condition, prev_baskets, penalties, task_name):
        moving_toward = 5 if self.distance(agent_pos, target_pos) < self.distance(prev_pos, target_pos) else 0
        close_to_target = 10 if self.distance(agent_pos, target_pos) < 1.0 else 0
        task_success = 10 if success_condition and not (len(prev_baskets) > 0 and prev_baskets[0]['owner'] == 0) else 0
        movement_penalty = -2 if agent_pos == prev_pos else 0  # Penalize staying still

        reward = moving_toward + close_to_target + task_success + movement_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"]

        logging.debug(f"{task_name} | Reward: {reward} | Moving: {moving_toward}, Close: {close_to_target}, "
                    f"Success: {task_success}, Norm: {penalties['norm']}, Exit: {penalties['exit']}, "
                    f"Cart: {penalties['cart']}, Movement: {movement_penalty}")
        return reward

    def reward_pick_basket(self, agent_pos, prev_pos, has_basket, prev_baskets, penalties):
        moving_toward = 5 if self.distance(agent_pos, basket_pos) < self.distance(prev_pos, basket_pos) else 0
        picked_basket = 15 if has_basket and not (len(prev_baskets) > 0 and prev_baskets[0]['owner'] == 0) else 0

        reward = moving_toward + picked_basket + penalties["norm"] + penalties["exit"] + penalties["cart"]

        logging.debug(f"Pick Basket | Reward: {reward} | Moving: {moving_toward}, Picked Basket: {picked_basket}, "
                    f"Norm: {penalties['norm']}, Exit: {penalties['exit']}, Cart: {penalties['cart']}")
        return reward

    def reward_navigate_shelf(self, state, prev_pos, agent_pos, target_item, penalties):
        shelf_pos = next(
            (shelf['position'] for shelf in state['observation']['shelves'] if shelf['food_name'] == target_item),
            None
        )

        if not shelf_pos:
            return penalties["norm"] + penalties["exit"] + penalties["cart"]

        moving_toward = 5 if self.distance(agent_pos, shelf_pos) < self.distance(prev_pos, shelf_pos) else 0
        close_to_shelf = 10 if self.distance(agent_pos, shelf_pos) < 0.6 else 0
        movement_penalty = -2 if agent_pos == prev_pos else 0  # Penalize staying still

        reward = moving_toward + close_to_shelf + movement_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"]

        logging.debug(f"Navigate Shelf | Item: {target_item} | Reward: {reward} | Moving: {moving_toward}, "
                    f"Close: {close_to_shelf}, Norm: {penalties['norm']}, Exit: {penalties['exit']}, "
                    f"Cart: {penalties['cart']}, Movement: {movement_penalty}")
        return reward

    def reward_pick_place(self, agent_pos, prev_pos, holding_food, target_item, current_basket_contents, prev_basket_contents, penalties):
        moving_toward = 5 if self.distance(agent_pos, prev_pos) < self.distance(prev_pos, agent_pos) else 0
        item_picked = 10 if holding_food and holding_food == target_item else 0
        wrong_item_penalty = -5 if holding_food and holding_food != target_item else 0
        item_placed_in_basket = 15 if len(current_basket_contents) > len(prev_basket_contents) else 0

        reward = moving_toward + item_picked + wrong_item_penalty + item_placed_in_basket + penalties["norm"] + penalties["exit"] + penalties["cart"]

        logging.debug(f"Pick & Place | Item: {target_item} | Reward: {reward} | Moving: {moving_toward}, Picked: {item_picked}, "
                    f"Wrong Item: {wrong_item_penalty}, Placed: {item_placed_in_basket}, "
                    f"Norm: {penalties['norm']}, Exit: {penalties['exit']}, Cart: {penalties['cart']}")
        return reward

    def send_action(self, action):
        action = f"0 {action}"  
        logging.debug(f"Sending action: {action}")

        try:
            self.sock.send(str.encode(action))
            output = recv_socket_data(self.sock)

            if not output:
                logging.warning("Received empty response from socket.")
                return {"observation": {"players": [{}]}, "gameOver": True}

            state = json.loads(output)
            pos = state['observation']['players'][0]['position']
            x = round(pos[0] / 0.05) * 0.05 
            y = round(pos[1] / 0.05) * 0.05  
            x, y = round(x, 2), round(y, 2)
            state['observation']['players'][0]['position'] = [x, y]
            return state

        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e} | Raw Data: {output}")
        except Exception as e:
            logging.error(f"Unexpected Error in send_action(): {e}")

        return {"observation": {"players": [{}]}, "gameOver": True}  # Fallback state

    def check_subtask_completion(self, subtask, state, target_item=None, threshold_enter=1.0, threshold_leave=4.0):
        agent_pos = state['observation']['players'][0]['position']
        baskets = state['observation']['baskets']
        has_basket = len(baskets) > 0 and baskets[0]['owner'] == 0
        current_basket_contents = baskets[0]['contents'] if has_basket else []

        if subtask == "navigate_basket":
            if self.distance(agent_pos, basket_pos) <= threshold_enter:
                logging.info(f"Subtask '{subtask}' completed: Arrived at basket.")
                return True

        elif subtask == "pick_basket":
            if has_basket:
                logging.info(f"Subtask '{subtask}' completed: Picked up basket.")
                return True
            if self.distance(agent_pos, basket_pos) > threshold_leave:
                logging.warning(f"Agent moved away from basket! Returning to 'navigate_basket'.")
                return "return_to_basket"

        elif subtask == "navigate_shelf" and target_item:
            for shelf in state['observation']['shelves']:
                if shelf['food_name'] == target_item: 
                    shelf_pos = shelf['position']
                    if self.distance(agent_pos, shelf_pos) <= threshold_enter:
                        logging.info(f"Subtask '{subtask}' completed: Reached shelf for {target_item}.")
                        return True

        elif subtask == "pick_place" and target_item:
            if target_item in current_basket_contents:
                logging.info(f"Subtask '{subtask}' completed: {target_item} placed in the basket.")
                return True
            for shelf in state['observation']['shelves']:
                if shelf['food_name'] == target_item:
                    shelf_pos = shelf['position']
                    if self.distance(agent_pos, shelf_pos) > threshold_leave:
                        logging.warning(f"Agent moved away from {target_item}'s shelf! Returning to 'navigate_shelf'.")
                        return "return_to_shelf"

        return False

    def execute_subtask(self, subtask, target_item):
        self.agent.reset_epsilon()
        state = self.send_action("NOP")  # Initial state retrieval
        logging.info(f"\n--- Executing Subtask: {subtask} | Target Item: {target_item if target_item else 'N/A'} ---\n")

        while not state['gameOver']:
            completion_status = self.check_subtask_completion(subtask, state, target_item)

            if completion_status == "return_to_basket":
                self.execute_subtask("navigate_basket", None)
                continue  

            if completion_status == "return_to_shelf":
                self.execute_subtask("navigate_shelf", target_item)
                continue  

            if completion_status:
                break  

            action_index = self.agent.choose_action(state, subtask)
            action = self.action_commands[action_index]

            logging.debug(f"Subtask: {subtask} | Selected Action: {action} | Current Position: {state['observation']['players'][0]['position']}")

            next_state = self.send_action(action)  
            reward = self.calculate_reward(next_state, state, subtask, target_item)

            logging.debug(f"Action Executed: {action} | Reward: {reward} | Next Position: {next_state['observation']['players'][0]['position']}")

            self.agent.learning(action_index, reward, state, next_state, subtask)

            try:
                qtable_path = f'qtables/{subtask}.json'
                self.agent.get_qtable(subtask).to_json(qtable_path)
                logging.debug(f"Q-table Updated: {qtable_path}")
            except Exception as e:
                logging.error(f"Failed to Save Q-table for {subtask} | Error: {e}")

            state = next_state  

        logging.info(f"\n--- Subtask '{subtask}' Completed ---\n")

    def train(self):
        for episode in range(self.episodes):
            self.send_action("RESET")  
            state = self.send_action("NOP")  

            shopping_planner = ShoppingPlanner(self.sock, state)
            ordered_shelves = shopping_planner.compute_shopping_order(state['observation']['players'][0]['shopping_list'][:6])

            logging.info(f"\n--- EPISODE {episode + 1}/{self.episodes} START ---\n")

            self.execute_subtask("navigate_basket", None)
            self.execute_subtask("pick_basket", None)  

            for item in ordered_shelves:
                self.execute_subtask("navigate_shelf", item)
                self.execute_subtask("pick_place", item)

            logging.info(f"\n--- EPISODE {episode + 1}/{self.episodes} COMPLETE ---\n")
            self.send_action("RESET")  

        self.sock.close()

if __name__ == "__main__":
    trainer = SupermarketTrainer()
    trainer.train()
