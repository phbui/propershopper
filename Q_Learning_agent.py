import numpy as np
import pandas as pd
import os
import logging

basket_pos = [3.5, 18.5]

class QLAgent:
    def __init__(self, action_space, alpha=0.5, gamma=0.8, epsilon=0.1, mini_epsilon=0.01, decay=0.999):
        self.action_space = action_space
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration-exploitation balance
        self.og_epsilon = epsilon
        self.mini_epsilon = mini_epsilon  # Minimum exploration probability
        self.decay = decay  # Epsilon decay over time

        # Directory for saving Q-tables
        self.qtable_dir = "qtables"
        os.makedirs(self.qtable_dir, exist_ok=True)

        # Store all Q-tables locally in a dictionary
        self.qtables = {
            "navigate_basket": self.load_qtable("navigate_basket"),
            "pick_basket": self.load_qtable("pick_basket"),
            "navigate_shelf": self.load_qtable("navigate_shelf"),
            "pick_place": self.load_qtable("pick_place"),
        }

        logging.info("\n--- Q-Learning Agent Initialized ---\n")
        logging.info(f"Action Space: {self.action_space} | Alpha: {self.alpha} | Gamma: {self.gamma} | "
                     f"Epsilon: {self.epsilon} | Decay: {self.decay}\n")

    def reset_epsilon(self):
        self.epsilon = self.og_epsilon

    def get_qtable(self, subtask):
        if subtask in self.qtables:
            return self.qtables[subtask]
        else:
            raise ValueError(f"Unknown subtask type: {subtask}")

    def trans(self, state, last_action, target_item, granularity=1):
        agent_pos = state['observation']['players'][0]['position']
        agent_pos = (round(agent_pos[0] / granularity) * granularity, round(agent_pos[1] / granularity) * granularity)
        agent_pos = [round(agent_pos[0], 2), round(agent_pos[1], 2)]

        cart = state['observation']['players'][0]['curr_cart']

        baskets = state['observation']['baskets']
        has_basket = 1 if (baskets and baskets[0]['owner'] == 0) else 0

        shopping_list = state['observation']['players'][0].get('shopping_list', [])
        next_item = shopping_list[0] if shopping_list else "NONE"

        target_pos = basket_pos if (not has_basket or target_item is None) else target_item[1]
        target_pos = [round(target_pos[0], 2), round(target_pos[1], 2)]

        state_key = f"{agent_pos}_{target_pos}_{last_action}_{has_basket}_{cart}_{next_item}"
        logging.debug(f"State Transformation | Agent: {agent_pos} | Target: {target_pos} | "
                      f"Basket: {has_basket} | Next Item: {next_item}")
        return state_key

    def learning(self, last_action, action, reward, state, next_state, subtask, target_item):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state, last_action, target_item)
        next_state_key = self.trans(next_state, last_action, target_item)

        action = int(action)

        if state_key not in qtable.index:
            qtable.loc[state_key] = np.zeros(self.action_space)

        if next_state_key not in qtable.index:
            qtable.loc[next_state_key] = np.zeros(self.action_space)

        max_future_q = np.max(qtable.loc[next_state_key])
        qtable.loc[state_key, action] = (1 - self.alpha) * qtable.loc[state_key, action] + \
                                        self.alpha * (reward + self.gamma * max_future_q)

        # Log the updated Q-values for debugging
        logging.debug(f"\n--- Q-Table Updated for {subtask} ---\n{qtable.head(100)}\n")

    def choose_action(self, last_action, state, subtask, target_item):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state, last_action, target_item)

        if state_key not in qtable.index:
            qtable.loc[state_key] = np.zeros(self.action_space)

        if np.random.rand() < self.epsilon:
            action = np.random.choice(self.action_space)  # Explore
        else:
            action = qtable.loc[state_key].idxmax()  # Exploit

        if self.epsilon > self.mini_epsilon:
            self.epsilon *= self.decay

        return action

    def save_qtable(self):
        for subtask, qtable in self.qtables.items():
            filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
            
            if not qtable.empty:
                qtable.to_json(filepath, orient="index")  # Explicitly store index as JSON keys
                logging.info(f"Saved Q-table to {filepath}")
                logging.debug(f"\n{qtable.head(100)}\n")
            else:
                logging.warning(f"Skipping save: Q-table for {subtask} is empty!")

    def load_qtable(self, subtask):
        filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
        if os.path.exists(filepath):
            qtable = pd.read_json(filepath, orient="index")  # Ensure correct index loading
            logging.info(f"Loaded Q-table from {filepath}")
            logging.info(f"\n{qtable.head(100)}\n")
            return qtable
        
        logging.info(f"Creating New Q-table: {subtask}")
        return pd.DataFrame(columns=[i for i in range(self.action_space)], dtype=np.float64).astype(float)
