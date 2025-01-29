import socket
from agent_class import Agent_Class
from Q_Learning_agent import QLAgent

class Agent_QLearn(Agent_Class):
    def __init__(self, sock_game, curr_player):
        super().__init__(sock_game, curr_player)
        self.agent = QLAgent(action_space=len(self.ACTION_COMMANDS))  # 7 actions

    def act(self, state):
        """Choose an action and send it to the environment."""
        action_index = self.agent.choose_action(state)
        action_command = self.ACTION_COMMANDS[action_index]
        return action_index, self.send_action(action_command)

    def update(self, action_index, reward, state, next_state):
        """Update Q-table after taking an action."""
        action_index = action_index  # Convert action to index
        self.agent.learning(action_index, reward, state, next_state)

    def get_reward(self, state, next_state, action_index):
        """Calculate reward based on state transitions."""
        player = state["players"][0]
        next_player = next_state["players"][0]

        # Player position
        x, y = player["position"]
        next_x, next_y = next_player["position"]

        # Carrot shelf position
        carrot_shelf_x, carrot_shelf_y = 11.5, 17.5

        # Distance before and after action
        prev_distance = abs(x - carrot_shelf_x) + abs(y - carrot_shelf_y)
        new_distance = abs(next_x - carrot_shelf_x) + abs(next_y - carrot_shelf_y)

        # Reward for moving toward the goal
        if new_distance < prev_distance:
            reward = 0.5  # Moved closer
        elif new_distance > prev_distance:
            reward = -0.5  # Moved away
        else:
            reward = -0.1  # Took a step but didn't move closer

        # Reward for picking up a carrot
        if player["holding_food"] is None and next_player["holding_food"] == "carrot":
            reward += 10  # Successfully grabbed carrot

        # Penalty for incorrect interaction
        if self.ACTION_COMMANDS[action_index] == "INTERACT" and next_player["holding_food"] is None:
            reward -= 5  # Tried to interact but failed

        return reward

    def restart_game(self):
        """Force restart by reconnecting to the server."""
        self.send_action("RESET")

    def run(self, episodes=100, save_interval=10):
        for episode in range(episodes):  # Number of training episodes
            self.restart_game()  # Reset environment at the start of each episode
            state = self.send_action("NOP")
            state = state["observation"]
            done = False
            
            while not done:
                action_index, next_state = self.act(state)  # Choose action
                next_state = next_state["observation"]
                reward = self.get_reward(state, next_state, action_index)
                self.update(action_index, reward, state, next_state)  # Q-learning update
                state = next_state 

            # Save Q-table every `save_interval` episodes
            if episode % save_interval == 0:
                print(f"Finished episode {episode}, saving...")
                self.agent.save_qtable()
