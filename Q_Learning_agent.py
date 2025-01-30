import numpy as np
import pandas as pd
import torch.nn.functional as F
import json  # Import json for dictionary serialization
import os

class QLAgent:
    # here are some default parameters, you can use different ones
    def __init__(self, action_space, alpha=0.5, gamma=0.8, epsilon=0.1, mini_epsilon=0.01, decay=0.999, qtable_path="qtable.json"):
        self.action_space = action_space 
        self.alpha = alpha               # learning rate
        self.gamma = gamma               # discount factor  
        self.epsilon = epsilon           # exploit vs. explore probability
        self.mini_epsilon = mini_epsilon # threshold for stopping the decay
        self.decay = decay               # value to decay the epsilon over time
        self.qtable_path = qtable_path
        self.qtable = self.load_qtable()

    def save_qtable(self):
        """Save Q-table to a JSON file."""
        with open(self.qtable_path, "w") as f:
            json.dump(self.qtable.to_dict(), f)
        print(f"Q-table saved to {self.qtable_path}")

    def load_qtable(self):
        """Load Q-table from a JSON file if it exists."""
        if os.path.exists(self.qtable_path):
            with open(self.qtable_path, "r") as f:
                data = json.load(f)
                qtable = pd.DataFrame.from_dict(data)

                for i in range(self.action_space):
                    if i not in qtable.columns:
                        qtable[i] = 0  # Initialize missing actions with zeros

                print(f"Q-table loaded from {self.qtable_path}")
                return qtable
        else:
            return pd.DataFrame(columns=[i for i in range(self.action_space)])
        
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
        """
        Update the Q-table using the Q-learning update rule:
        
        Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
        
        where:
        - s  = current state
        - a  = action taken
        - s' = next state
        - a' = future action (which maximizes Q-value)
        - α (alpha) = learning rate (0 < α ≤ 1)
        - γ (gamma) = discount factor (0 < γ ≤ 1)
        - r = reward received after taking action a in state s
        - max(Q(s', a')) = estimated future reward from the best possible action in the next state

        This equation adjusts the Q-value estimate for (s, a) by incorporating the immediate reward (r)
        and the best possible future Q-value (discounted by γ). The difference term inside the brackets 
        is known as the temporal difference (TD) error.
        """
        
        # Convert state and next_state to hashable string keys for indexing in Q-table
        s = str(tuple(self.trans(state)))       
        s_prime = str(tuple(self.trans(next_state)))

        # Ensure Q-table includes both the current state (s) and next state (s')
        if s not in self.qtable.index:
            self.qtable.loc[s] = np.zeros(self.action_space)  # Initialize with zeros
        if s_prime not in self.qtable.index:
            self.qtable.loc[s_prime] = pd.Series(np.zeros(self.action_space), index=self.qtable.columns)

        # Find the best estimated Q-value for next state s' (i.e., max Q(s', a'))
        best_next_q = np.max(self.qtable.loc[s_prime])  # max_a' Q(s', a')

        # Compute the Q-learning update:
        # Q(s, a) = Q(s, a) + α * (r + γ * max(Q(s', a')) - Q(s, a))
        self.qtable.loc[s, action] = float(self.qtable.loc[s, action]) + self.alpha * (rwd + self.gamma * best_next_q - self.qtable.loc[s, action])

        # Decay epsilon to reduce exploration over time, ensuring more exploitation of learned knowledge
        self.epsilon = max(self.mini_epsilon, self.epsilon * self.decay)

    def choose_action(self, state):
        """
        Selects an action using an epsilon-greedy strategy:
        
        - With probability ε (epsilon), pick a random action (exploration)
        - With probability 1 - ε, pick the best known action (exploitation)

        This ensures a balance between trying new actions and using learned knowledge.
        """
        
        # Convert state into a hashable string key for indexing in Q-table
        s = str(tuple(self.trans(state)))

        # If the state is new (not in Q-table), initialize its Q-values to zero
        if s not in self.qtable.index:
            self.qtable.loc[s] = np.zeros(self.action_space)

        # Exploration-Exploitation Trade-off:
        if np.random.rand() < self.epsilon:
            # Choose a random action with probability epsilon (ε) → EXPLORATION
            return np.random.choice(self.action_space)
        else:
            # Choose the best known action (highest Q-value) with probability (1 - ε) → EXPLOITATION
            return np.argmax(self.qtable.loc[s])  # argmax_a Q(s, a)
