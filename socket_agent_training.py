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

exit_pos = [-0.8, 15.6]
cart_pos_left = [1, 18.5]
cart_pos_right = [2, 18.5]

# Logging setup: logs to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to chat
    ]
)

class SupermarketTrainer:
    def __init__(self, host='127.0.0.1', port=9000, episodes=100, episode_length=1000):
        self.action_commands = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'INTERACT']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.agent = QLAgent(action_space=len(self.action_commands) - 1)
        self.episodes = episodes
        self.episode_length = episode_length

    def distance(self, pos1, pos2):
        return np.linalg.norm(np.array(pos1) - np.array(pos2))

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

        exit_distance = self.distance(agent_pos, exit_pos)
        exit_penalty = -10 if exit_distance < 2.0 else -5 if exit_distance < 4.0 else 0

        cart_penalty = sum([-10 if self.distance(agent_pos, cart['position']) < 1.5 else 0 for cart in carts])

        norm_penalty = sum([
            -10 if "BlockingShelfNorm" in violations else 0,
            -15 if "WallCollisionViolation" in violations else 0,
            -20 if "PlayerCollisionNorm" in violations else 0,
            -10 if "ObjectCollisionNorm" in violations else 0
        ])

        logging.info(f"\n--- Subtask: {subtask} ---\nPosition: {agent_pos} | Holding: {holding_food} | Basket: {has_basket} | Violations: {violations} | Exit Distance: {exit_distance}\n")

        if subtask == "navigate_basket":
            basket_pos = [3.5, 18.5]
            reward = (5 if self.distance(agent_pos, basket_pos) < self.distance(prev_pos, basket_pos) else 0) + \
                     (10 if self.distance(agent_pos, basket_pos) < 1.0 else 0) + \
                     (10 if has_basket and not (len(prev_baskets) > 0 and prev_baskets[0]['owner'] == 0) else 0) + \
                     norm_penalty + exit_penalty + cart_penalty - (1 if agent_pos == prev_pos else 0)
            logging.info(f"Navigate Basket | Reward Breakdown: {reward} (Norm: {norm_penalty}, Exit: {exit_penalty}, Cart: {cart_penalty})")
            return reward

        if subtask == "navigate_shelf" and target_item:
            for shelf in state['observation']['shelves']:
                if shelf['food_name'] == target_item:
                    shelf_pos = shelf['position']
                    break
            else:
                return norm_penalty + exit_penalty + cart_penalty

            reward = (5 if self.distance(agent_pos, shelf_pos) < self.distance(prev_pos, shelf_pos) else 0) + \
                     (10 if self.distance(agent_pos, shelf_pos) < 0.6 else 0) + \
                     norm_penalty + exit_penalty + cart_penalty - (1 if agent_pos == prev_pos else 0)
            logging.info(f"Navigate Shelf | Item: {target_item} | Reward Breakdown: {reward}")
            return reward

        if subtask == "pick_place" and target_item:
            reward = (10 if holding_food and holding_food == target_item else 0) - \
                     (5 if holding_food and holding_food != target_item else 0) + \
                     (15 if len(current_basket_contents) > len(prev_basket_contents) else 0) + \
                     norm_penalty + exit_penalty + cart_penalty
            logging.info(f"Pick & Place | Item: {target_item} | Reward Breakdown: {reward}")
            return reward

        return norm_penalty + exit_penalty + cart_penalty

    def send_action(self, action):
        """Send an action and return the resulting state."""
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

    def execute_subtask(self, subtask, episode_length, target_item=None):
        """Execute a subtask, updating state only through `send_action`."""
        cnt = 0
        state = self.send_action("NOP")  # Initial state retrieval

        logging.info(f"\n--- Executing Subtask: {subtask} | Target Item: {target_item if target_item else 'N/A'} ---\n")

        while not state['gameOver'] and cnt < episode_length:
            cnt += 1
            action_index = self.agent.choose_action(state, subtask)
            action = self.action_commands[action_index]

            logging.debug(f"Step {cnt} | Subtask: {subtask} | Selected Action: {action} | Current Position: {state['observation']['players'][0]['position']}")

            next_state = self.send_action(action)  # Send action and receive updated state
            reward = self.calculate_reward(next_state, state, subtask, target_item)

            logging.debug(f"Step {cnt} | Action Executed: {action} | Reward: {reward} | Next Position: {next_state['observation']['players'][0]['position']}")

            self.agent.learning(action_index, reward, state, next_state, subtask)

            try:
                qtable_path = f'qtables/{subtask}.json'
                self.agent.get_qtable(subtask).to_json(qtable_path)
                logging.debug(f"Step {cnt} | Q-table Updated: {qtable_path}")
            except Exception as e:
                logging.error(f"Step {cnt} | Failed to Save Q-table for {subtask} | Error: {e}")

            state = next_state  # Update state for next iteration

        logging.info(f"\n--- Subtask {subtask} Completed | Total Steps: {cnt} ---\n")

    def train(self):
        """Run the training loop, handling state updates through `send_action`."""
        for episode in range(self.episodes):
            self.send_action("RESET")  # Reset environment
            state = self.send_action("NOP")  # Retrieve initial state

            shopping_planner = ShoppingPlanner(self.sock, state)
            ordered_shelves = shopping_planner.compute_shopping_order(['strawberry milk', 'raspberry', 'cucumber', 'milk', 'swiss cheese'])

            logging.info(f"\n--- EPISODE {episode + 1}/{self.episodes} START ---\n")

            self.execute_subtask("navigate_basket", self.episode_length)

            for item in ordered_shelves:
                logging.info(f"\nNavigating to Shelf for Item: {item}\n")
                self.execute_subtask("navigate_shelf", self.episode_length, item)

                logging.info(f"\nPicking and Placing Item: {item}\n")
                self.execute_subtask("pick_place", self.episode_length, item)

            self.execute_subtask("navigate_basket", self.episode_length)
            self.send_action("INTERACT")

            logging.info(f"\n--- EPISODE {episode + 1}/{self.episodes} COMPLETE ---\n")
            self.send_action("RESET")  # Reset for next episode

        self.sock.close()

if __name__ == "__main__":
    trainer = SupermarketTrainer()
    trainer.train()
