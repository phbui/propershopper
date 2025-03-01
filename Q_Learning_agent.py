import numpy as np
import pandas as pd
import os
import logging


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

    def trans(self, state, granularity=0.5):
        agent_pos = state['observation']['players'][0]['position']
        basket_pos = [3.5, 18.5]  # Assume basket is at a fixed location

        # Get the target shelf position
        shopping_list = state['observation']['players'][0]['shopping_list']
        shelf_pos = (0.0, 0.0)  # Default shelf position if not found

        if shopping_list:
            target_item = shopping_list[0]  # Focus on the first item in the list
            for shelf in state['observation']['shelves']:
                if shelf['food_name'] == target_item:
                    shelf_pos = shelf['position']
                    break

        # Discretize positions
        agent_pos = (round(agent_pos[0] / granularity) * granularity, round(agent_pos[1] / granularity) * granularity)
        shelf_pos = (round(shelf_pos[0] / granularity) * granularity, round(shelf_pos[1] / granularity) * granularity)
        basket_pos = (round(basket_pos[0] / granularity) * granularity, round(basket_pos[1] / granularity) * granularity)

        holding_item = 1 if state['observation']['players'][0]['holding_food'] else 0
        remaining_items = len(shopping_list)

        # Convert state_key to a string (hashable)
        state_key = f"{agent_pos}_{shelf_pos}_{basket_pos}_{holding_item}_{remaining_items}"

        logging.debug(f"State Transformation | Raw: {state['observation']['players'][0]['position']} | Transformed: {state_key}")
        return state_key  # Return a string representation

    def learning(self, action, reward, state, next_state, subtask):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state)
        next_state_key = self.trans(next_state)

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

    def choose_action(self, state, subtask):
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state)

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
