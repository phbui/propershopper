import socket
from agent_class import Agent_Class
from Q_Learning_agent import QLAgent

class Agent_QLearn(Agent_Class):
    ACTION_COMMANDS = [
        'INTERACT', 'TOGGLE_CART',
        'TURN_NORTH', 'TURN_SOUTH', 'TURN_EAST', 'TURN_WEST',
        'MOVE_NORTH', 'MOVE_SOUTH', 'MOVE_EAST', 'MOVE_WEST'
    ]

    def __init__(self, sock_game, curr_player):
        super().__init__(sock_game, curr_player)
        self.agent = QLAgent(action_space=len(self.ACTION_COMMANDS))

    def translate_command(self, command):
        if command.startswith("TURN_"):
            return [command.replace("TURN_", "")]  # Remove "TURN_" prefix and send once
        
        elif command.startswith("MOVE_"):
            return [command.replace("MOVE_", ""), command.replace("MOVE_", "")]  # Send movement twice
        
        else:
            return [command]  

    def act(self, state):
        """Choose an action and send it to the environment."""
        action_index = self.agent.choose_action(state)
        action_commands = self.translate_command(self.ACTION_COMMANDS[action_index])
        result = None
        for action in action_commands:
            result = self.send_action(action)  # Send each translated action separately
        return action_index, result

    def update(self, action_index, reward, state, next_state):
        """Update Q-table after taking an action."""
        action_index = action_index  # Convert action to index
        self.agent.learning(action_index, reward, state, next_state)

    def get_reward(self, state, next_state, action_index):
        """Calculate reward based on Manhattan distance, interactions, and rule violations."""
        player = state["observation"]["players"][0]
        next_player = next_state["observation"]["players"][0]

        # Player position
        x, y = player["position"]
        next_x, next_y = next_player["position"]

        # Carrot shelf position (goal)
        carrot_shelf_x, carrot_shelf_y = 11.5, 17.5

        # Compute Manhattan distance before and after the action
        prev_distance = abs(x - carrot_shelf_x) + abs(y - carrot_shelf_y)
        new_distance = abs(next_x - carrot_shelf_x) + abs(next_y - carrot_shelf_y)

        # Reward based on Manhattan distance improvement
        distance_reward = (prev_distance - new_distance)  # Positive if moving closer, negative if moving away

        # Scale reward to encourage faster movement
        reward = 1.1 * distance_reward  # Multiplier controls how much distance affects learning

        # Negative reward for staying in the same position (unless very close to the goal)
        if (x, y) == (next_x, next_y):
            if new_distance > 1:  # If not near goal, punish staying still
                reward -= 2  
            else:  # If near goal, staying is neutral
                reward += 0  

        # Negative reward for rule violations
        if len(state["violations"]) > 0:
            reward -= 5 * len(state["violations"])  # Each violation carries a penalty

        # Reward for successfully picking up a carrot
        if player["holding_food"] is None and next_player["holding_food"] == "carrot":
            reward += 10  # High reward for goal completion

        # Penalty for incorrect interaction
        if self.ACTION_COMMANDS[action_index] == "INTERACT" and next_player["holding_food"] is None:
            reward -= 5  # Discourage unnecessary interactions

        return reward

    def restart_game(self):
        """Force restart by reconnecting to the server."""
        self.send_action("RESET")

    def run(self, episodes=100, save_interval=10):
        for episode in range(episodes):  # Number of training episodes
            self.restart_game()  # Reset environment at the start of each episode
            state = self.send_action("NOP")
            done = False
            
            while not done:
                action_index, next_state = self.act(state["observation"])  # Choose action
                reward = self.get_reward(state, next_state, action_index)
                self.update(action_index, reward, state["observation"], next_state["observation"])  # Q-learning update
                state = next_state 

            # Save Q-table every `save_interval` episodes
            if episode % save_interval == 0:
                print(f"Finished episode {episode}, saving...")
                self.agent.save_qtable()
