import numpy as np
import pandas as pd
import os
import logging

basket_pos = [3.5, 18.5]

class QLAgent:
    def __init__(self, action_space, alpha=0.5, gamma=0.8, epsilon=0.5, mini_epsilon=0.01, decay=0.999):
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

        # Load or initialize separate Q-tables for different subtasks
        self.qtable_navigate_basket = self.load_qtable("navigate_basket")
        self.qtable_pick_basket = self.load_qtable("pick_basket")

        self.qtable_navigate_shelf = self.load_qtable("navigate_shelf")
        self.qtable_pick_place = self.load_qtable("pick_place")

        logging.info("\n--- Q-Learning Agent Initialized ---\n")
        logging.info(f"Action Space: {self.action_space} | Alpha: {self.alpha} | Gamma: {self.gamma} | Epsilon: {self.epsilon} | Decay: {self.decay}\n")

    def reset_epsilon(self):
        self.epsilon = self.og_epsilon

    def get_qtable(self, subtask):
        if subtask == "navigate_basket":
            return self.qtable_navigate_basket
        elif subtask == "pick_basket":
            return self.qtable_pick_basket
        elif subtask == "navigate_shelf":
            return self.qtable_navigate_shelf
        elif subtask == "pick_place":
            return self.qtable_pick_place
        else:
            raise ValueError(f"Unknown subtask type: {subtask}")

    def trans(self, state, target_item, granularity=0.15):
        # Get agent's position
        agent_pos = state['observation']['players'][0]['position']
        agent_pos = (round(agent_pos[0] / granularity) * granularity, round(agent_pos[1] / granularity) * granularity)
        x = round(agent_pos[0] / 0.05) * 0.05 
        y = round(agent_pos[1] / 0.05) * 0.05  
        agent_pos = [round(x, 2), round(y, 2)]

        # Check if agent has a basket
        baskets = state['observation']['baskets']
        has_basket = 1 if (baskets and baskets[0]['owner'] == 0) else 0

        # Get the next item in the shopping list
        shopping_list = state['observation']['players'][0].get('shopping_list', [])
        next_item = shopping_list[0] if shopping_list else "NONE"

        if not has_basket or target_item is None:
            target_pos = basket_pos  # Go to basket first
        else:
            target_pos = target_item[0][1]

        # Discretize target position
        target_pos = (round(target_pos[0] / granularity) * granularity, round(target_pos[1] / granularity) * granularity)
        x = round(target_pos[0] / 0.05) * 0.05 
        y = round(target_pos[1] / 0.05) * 0.05  
        target_pos = [round(x, 2), round(y, 2)]

        # Convert state into a string key (hashable)
        state_key = f"{agent_pos}_{target_pos}_{has_basket}_{next_item}"

        logging.debug(f"State Transformation | Agent: {agent_pos} | Target: {target_pos} | Basket: {has_basket} | Next Item: {next_item}")
        return state_key

    def learning(self, action, reward, state, next_state, subtask, target_item):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state, target_item)
        next_state_key = self.trans(next_state, target_item)

        if state_key not in qtable.index:
            qtable.loc[state_key] = np.zeros(self.action_space)

        if next_state_key not in qtable.index:
            qtable.loc[next_state_key] = np.zeros(self.action_space)

        # Q-learning update rule
        max_future_q = np.max(qtable.loc[next_state_key])
        current_q = qtable.loc[state_key, action]
        qtable.loc[state_key, action] += self.alpha * (reward + self.gamma * max_future_q - current_q)

        # Save the updated Q-table
        self.save_qtable(qtable, subtask)

    def choose_action(self, state, subtask, target_item):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state, target_item)

        # Ensure the key exists in the Q-table before accessing it
        if state_key not in qtable.index:
            qtable.loc[state_key] = np.zeros(self.action_space)  # Initialize new row

        # Exploration vs. Exploitation
        if np.random.rand() < self.epsilon:
            action = np.random.choice(self.action_space)  # Explore
        else:
            action = qtable.loc[state_key].idxmax()  # Exploit

        # Decay epsilon
        if self.epsilon > self.mini_epsilon:
            self.epsilon *= self.decay

        return action

    def save_qtable(self, qtable, subtask):
        filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
        qtable.to_json(filepath)
        logging.debug(f"Saved Q-table: {filepath}")

    def load_qtable(self, subtask):
        filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
        if os.path.exists(filepath):
            logging.info(f"Loading Q-table: {filepath}")
            return pd.read_json(filepath)
        logging.info(f"Creating New Q-table: {subtask}")
        return pd.DataFrame(columns=[i for i in range(self.action_space)])
