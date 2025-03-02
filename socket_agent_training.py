import json
import socket
import numpy as np
import logging
import sys

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
        self.action_commands = [
                'INTERACT',
                'TURN_NORTH', 'TURN_SOUTH', 'TURN_EAST', 'TURN_WEST',
                'MOVE_NORTH', 'MOVE_SOUTH', 'MOVE_EAST', 'MOVE_WEST'
            ]
        self.direction_map = {0: "NORTH", 1: "SOUTH", 2: "EAST", 3: "WEST"}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.agent = QLAgent(action_space=len(self.action_commands) - 1)
        self.episodes = episodes
        self.last_action_index = -1

    def translate_command(self, state, command):
        direction = state['observation']['players'][0]["direction"]
        
        if command.startswith("TURN_"):
            new_command = command.replace("TURN_", "")
            if (self.direction_map[direction] != new_command):
                return [new_command]  # Remove "TURN_" prefix and send once
            else:
                return ["NOP"]
        
        elif command.startswith("MOVE_"):
            new_command = command.replace("MOVE_", "")
            if (self.direction_map[direction] == new_command):
                return [new_command]
            else:
                return [new_command, new_command]  # Send movement twice
        
        else:
            return [command]  

    def distance(self, a, b):
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def calculate_reward(self, action_index, state, prev_state, subtask, target_item=None):
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
        penalties = self.compute_penalties(action_index, agent_pos, carts, violations)

        # Apply appropriate subtask reward calculation
        if subtask == "navigate_basket":
            return self.reward_navigate_basket(agent_pos, prev_pos, penalties, action_index)

        if subtask == "pick_basket":
            return self.reward_pick_basket(agent_pos, prev_pos, has_basket, penalties, action_index)

        if subtask == "navigate_shelf" and target_item:
            return self.reward_navigate_shelf(prev_pos, agent_pos, target_item, penalties, action_index)

        if subtask == "pick_place" and target_item:
            return self.reward_pick_place(agent_pos, prev_pos, holding_food, target_item, current_basket_contents, prev_basket_contents, penalties, action_index)

        return penalties["norm"] + penalties["exit"] + penalties["cart"]

    def compute_penalties(self, action_index, agent_pos, carts, violations):
        exit_distance = self.distance(agent_pos, exit_pos)
        exit_penalty = -10 if exit_distance < 2.0 else -5 if exit_distance < 4.0 else 0

        cart_penalty = sum([-10 if self.distance(agent_pos, cart['position']) < 1.5 else 0 for cart in carts])

        opposites = {
            5: 6,  
            6: 5,  
            7: 8,  
            8: 7   
        }

        action_penalty = -50 if self.last_action_index in opposites and opposites.get(self.last_action_index) == action_index else 0

        norm_penalty = sum([
            -10 if "BlockingShelfNorm" in violations else 0,
            -15 if "WallCollisionViolation" in violations else 0,
            -20 if "PlayerCollisionNorm" in violations else 0,
            -10 if "ObjectCollisionNorm" in violations else 0
        ])

        return {"norm": norm_penalty, "exit": exit_penalty, "cart": cart_penalty, "action": action_penalty}
    
    def reward_navigate_basket(self, agent_pos, prev_pos, penalties, action_index):
        current_distance = self.distance(agent_pos, basket_pos)
        prev_distance = self.distance(prev_pos, basket_pos)
        delta = prev_distance - current_distance
        delta_reward = 50 * delta
        bonus = 100 if current_distance < 1.0 else 0
        # If the agent does not change its distance (i.e. delta is 0), apply a penalty.
        stagnation_penalty = -20 if abs(delta) < 1e-5 else 0

        action_score = 10 if delta > 1e-5 else penalties["action"]
        reward = delta_reward + bonus + stagnation_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"] + action_score

        logging.info(f"Navigate Basket | {self.action_commands[action_index]} | Prev: {prev_pos} | Curr: {agent_pos} | Reward: {reward} | Delta Reward: {delta_reward}, Bonus: {bonus}, "
                    f"Stagnation Penalty: {stagnation_penalty}, Norm: {penalties['norm']}, "
                    f"Exit: {penalties['exit']}, Cart: {penalties['cart']}, Action: {action_score}")
        return reward

    def reward_pick_basket(self, agent_pos, prev_pos, has_basket, penalties, action_index):
        current_distance = self.distance(agent_pos, basket_pos)
        prev_distance = self.distance(prev_pos, basket_pos)
        delta = prev_distance - current_distance
        delta_reward = 50 * delta
        pick_reward = 100 if has_basket else 0
        stagnation_penalty = -20 if abs(delta) < 1e-5 else 0

        action_score = 10 if delta > 0 else penalties["action"]
        reward = delta_reward + pick_reward + stagnation_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"] + action_score

        logging.info(f"Pick Basket | {self.action_commands[action_index]} | Prev: {prev_pos} | Curr: {agent_pos} | Reward: {reward} | Delta Reward: {delta_reward}, "
                    f"Picked: {pick_reward}, Stagnation: {stagnation_penalty}, "
                    f"Norm: {penalties['norm']}, Exit: {penalties['exit']}, Cart: {penalties['cart']}, Action: {action_score}")
        return reward

    def reward_navigate_shelf(self, prev_pos, agent_pos, target_item, penalties, action_index):
        # Assume target_item is a tuple: (item_name, target_position)
        shelf_pos = target_item[1]
        current_distance = self.distance(agent_pos, shelf_pos)
        prev_distance = self.distance(prev_pos, shelf_pos)
        delta = prev_distance - current_distance
        delta_reward = 50 * delta
        bonus = 100 if current_distance < 1.0 else 0
        stagnation_penalty = -20 if abs(delta) < 1e-5 else 0

        action_score = 10 if delta > 0 else penalties["action"]
        reward = delta_reward + bonus + stagnation_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"] + action_score

        logging.info(f"Navigate Shelf | {self.action_commands[action_index]} | Prev: {prev_pos} | Curr: {agent_pos} | Item: {target_item[0]} | Reward: {reward} | Delta Reward: {delta_reward}, "
                    f"Bonus: {bonus}, Stagnation: {stagnation_penalty}, Norm: {penalties['norm']}, "
                    f"Exit: {penalties['exit']}, Cart: {penalties['cart']}, Action: {action_score}")
        return reward

    def reward_pick_place(self, agent_pos, prev_pos, holding_food, target_item, current_basket_contents, prev_basket_contents, penalties, action_index):
        shelf_pos = target_item[1]
        current_distance = self.distance(agent_pos, shelf_pos)
        prev_distance = self.distance(prev_pos, shelf_pos)
        delta = prev_distance - current_distance
        delta_reward = 50 * delta
        item_picked = 10 if holding_food and holding_food == target_item[0] else 0
        wrong_item_penalty = -10 if holding_food and holding_food != target_item[0] else 0
        placed_bonus = 100 if len(current_basket_contents) > len(prev_basket_contents) else 0
        stagnation_penalty = -20 if abs(delta) < 1e-5 else 0

        action_score = 10 if delta > 0 else penalties["action"]
        reward = delta_reward + item_picked + wrong_item_penalty + placed_bonus + stagnation_penalty + penalties["norm"] + penalties["exit"] + penalties["cart"] + action_score

        logging.info(f"Pick & Place | {self.action_commands[action_index]} | Item: {target_item[0]} | Prev: {prev_pos} | Curr: {agent_pos} | Reward: {reward} | Delta Reward: {delta_reward}, "
                    f"Picked: {item_picked}, Wrong: {wrong_item_penalty}, Placed: {placed_bonus}, "
                    f"Stagnation: {stagnation_penalty}, Norm: {penalties['norm']}, Exit: {penalties['exit']}, "
                    f"Cart: {penalties['cart']}, Action: {action_score}")
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

    def check_subtask_completion(self, subtask, state, target_item=None, threshold_enter=1.0, threshold_leave=3.0):
        agent_pos = state['observation']['players'][0]['position']
        baskets = state['observation']['baskets']
        has_basket = len(baskets) > 0 and baskets[0]['owner'] == 0
        current_basket_contents = baskets[0]['contents'] if has_basket else []

        if subtask == "navigate_basket":
            if self.distance(agent_pos, basket_pos) <= threshold_enter:
                logging.info(f"Subtask '{subtask}' completed: Arrived at basket.")
                self.agent.save_qtable()
                return True

        elif subtask == "pick_basket":
            if has_basket:
                logging.info(f"Subtask '{subtask}' completed: Picked up basket.")
                self.agent.save_qtable()
                return True
            if self.distance(agent_pos, basket_pos) > threshold_leave:
                logging.warning(f"Agent moved away from basket! Returning to 'navigate_basket'.")
                return "return_to_basket"

        elif subtask == "navigate_shelf" and target_item:
            if self.distance(agent_pos, target_item[1]) <= threshold_enter:
                logging.info(f"Subtask '{subtask}' completed: Reached shelf for {target_item}.")
                self.agent.save_qtable()
                return True

        elif subtask == "pick_place" and target_item:
            if target_item in current_basket_contents:
                logging.info(f"Subtask '{subtask}' completed: {target_item} placed in the basket.")
                self.agent.save_qtable()
                return True
            if self.distance(agent_pos, target_item[1]) > threshold_leave:
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

            action_index, best = self.agent.choose_action(self.last_action_index, state, subtask, target_item)
            action = self.action_commands[action_index]
            actions = self.translate_command(state, action)
            next_state = {}

            for a in actions:
                next_state = self.send_action(a)

            reward = self.calculate_reward(action_index, next_state, state, subtask, target_item)

            logging.debug(f"Subtask: {subtask} | Action Executed: {action} | Best?: {best} | Reward: {reward}")
               
            self.agent.learning(self.last_action_index, action_index, reward, state, next_state, subtask, target_item)
            state = next_state  
            self.last_action_index = action_index

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
