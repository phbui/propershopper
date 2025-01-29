import numpy as np
import pandas as pd
import torch.nn.functional as F
import json  # Import json for dictionary serialization

class QLAgent:
    # here are some default parameters, you can use different ones
    def __init__(self, action_space, alpha=0.5, gamma=0.8, epsilon=0.1, mini_epsilon=0.01, decay=0.999):
        self.action_space = action_space 
        self.alpha = alpha               # learning rate
        self.gamma = gamma               # discount factor  
        self.epsilon = epsilon           # exploit vs. explore probability
        self.mini_epsilon = mini_epsilon # threshold for stopping the decay
        self.decay = decay               # value to decay the epsilon over time
        self.qtable = pd.DataFrame(columns=[i for i in range(self.action_space)])  # generate the initial table
    
    def trans(self, state, granularity=0.5):
        """Transform raw environment state into a learnable Q-table state."""
        player = state["players"][0]
        player_x, player_y = player["position"]
        direction = player["direction"]
        holding_food = player["holding_food"]
        
        # Convert position to discrete grid points
        player_x = round(player_x / granularity) * granularity
        player_y = round(player_y / granularity) * granularity

        # Carrot shelf position (known in advance)
        carrot_shelf_x, carrot_shelf_y = 11.5, 17.5

        # Compute Manhattan distance to carrot shelf
        distance = abs(player_x - carrot_shelf_x) + abs(player_y - carrot_shelf_y)
        near_shelf = 1 if distance <= 3 else 0  # Binary indicator (near/far)

        # Facing the correct direction (North=0, South=1)
        correct_facing = 1 if direction in [0, 1] else 0

        # Holding carrot (1) or not (0)
        has_carrot = 1 if holding_food == "carrot" else 0

        # Discrete state representation
        return (player_x, player_y, direction, near_shelf, correct_facing, has_carrot)
        
    def learning(self, action, rwd, state, next_state):
        """Update Q-table using Q-learning formula."""
        s = str(tuple(self.trans(state)))       # Convert state to string for indexing
        s_prime = str(tuple(self.trans(next_state)))

        # Ensure Q-table includes both current and next state
        if s not in self.qtable.index:
            self.qtable.loc[s] = np.zeros(self.action_space)
        if s_prime not in self.qtable.index:
            self.qtable.loc[s_prime] = np.zeros(self.action_space)

        # Q-learning update rule
        best_next_q = np.max(self.qtable.loc[s_prime])  # Best future Q-value
        self.qtable.loc[s, action] += self.alpha * (rwd + self.gamma * best_next_q - self.qtable.loc[s, action])

        # Decay epsilon for less exploration over time
        self.epsilon = max(self.mini_epsilon, self.epsilon * self.decay)


    def choose_action(self, state):
        """Select an action using an epsilon-greedy policy."""
        s = str(tuple(self.trans(state)))   # Convert state
        
        # If state is new, initialize Q-values
        if s not in self.qtable.index:
            self.qtable = pd.concat([self.qtable, pd.DataFrame([np.zeros(self.action_space)], index=[s])])
                
        # Exploration-exploitation trade-off
        if np.random.rand() < self.epsilon:
            return np.random.choice(self.action_space)  # Random action (explore)
        else:
            return np.argmax(self.qtable.loc[s])  # Best known action (exploit)
