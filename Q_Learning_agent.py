import numpy as np
import pandas as pd
import json
import os

class QLAgent:
    def __init__(self, action_space, alpha=0.5, gamma=0.8, epsilon=0.1, mini_epsilon=0.01, decay=0.999):
        self.action_space = action_space
        self.alpha = alpha               # Learning rate
        self.gamma = gamma               # Discount factor
        self.epsilon = epsilon           # Exploration-exploitation balance
        self.mini_epsilon = mini_epsilon # Minimum exploration probability
        self.decay = decay               # Epsilon decay over time

        # Directory for saving Q-tables
        self.qtable_dir = "qtables"
        os.makedirs(self.qtable_dir, exist_ok=True)

        # Load or initialize separate Q-tables for different subtasks
        self.qtable_navigate_basket = self.load_qtable("navigate_basket")
        self.qtable_navigate_shelf = self.load_qtable("navigate_shelf")
        self.qtable_pick_place = self.load_qtable("pick_place")

    def get_qtable(self, subtask):
        """Returns the appropriate Q-table for a given subtask."""
        if subtask == "navigate_basket":
            return self.qtable_navigate_basket
        elif subtask == "navigate_shelf":
            return self.qtable_navigate_shelf
        elif subtask == "pick_place":
            return self.qtable_pick_place
        else:
            raise ValueError("Unknown subtask type")

    def trans(self, state, granularity=0.5):
        """Transform the raw state into a learnable Q-table state."""
        agent_pos = state['observation']['players'][0]['position']
        basket_pos = [3.5, 18.5]  # Assume basket is at a fixed location

        # Get the target shelf position
        shopping_list = state['observation']['players'][0]['shopping_list']
        shelf_pos = None
        if shopping_list:
            target_item = shopping_list[0]  # Focus on the first item in the list
            for shelf in state['observation']['shelves']:
                if shelf['food_name'] == target_item:
                    shelf_pos = shelf['position']
                    break

        if not shelf_pos:
            shelf_pos = (0, 0)  # Default shelf position

        # Discretize positions
        agent_pos = (round(agent_pos[0] / granularity) * granularity, round(agent_pos[1] / granularity) * granularity)
        shelf_pos = (round(shelf_pos[0] / granularity) * granularity, round(shelf_pos[1] / granularity) * granularity)
        basket_pos = (round(basket_pos[0] / granularity) * granularity, round(basket_pos[1] / granularity) * granularity)

        holding_item = 1 if state['observation']['players'][0]['holding_food'] else 0
        remaining_items = len(shopping_list)

        return (agent_pos, shelf_pos, basket_pos, holding_item, remaining_items)

    def learning(self, action, reward, state, next_state, subtask):
        """Q-learning update rule."""
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
        """Select an action using ε-greedy policy."""
        qtable = self.get_qtable(subtask)
        state_key = self.trans(state)

        if state_key not in qtable.index:
            qtable.loc[state_key] = np.zeros(self.action_space)

        # Exploration vs Exploitation
        if np.random.rand() < self.epsilon:
            action = np.random.choice(self.action_space)  # Explore
        else:
            action = qtable.loc[state_key].idxmax()  # Exploit

        # Decay epsilon
        if self.epsilon > self.mini_epsilon:
            self.epsilon *= self.decay

        return action

    def save_qtable(self, qtable, subtask):
        """Save the Q-table to a JSON file."""
        filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
        qtable.to_json(filepath)

    def load_qtable(self, subtask):
        """Load the Q-table from a JSON file if it exists, else create a new one."""
        filepath = os.path.join(self.qtable_dir, f"{subtask}.json")
        if os.path.exists(filepath):
            return pd.read_json(filepath)
        return pd.DataFrame(columns=[i for i in range(self.action_space)])
