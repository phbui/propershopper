import numpy as np
from utils import recv_socket_data
import json
from queue import PriorityQueue
import logging

objs = [
    {'height': 2.5, 'width': 3, 'position': [0.2, 4.5], 're_centered_position': [2.125, 5.75]},
    {'height': 2.5, 'width': 3, 'position': [0.2, 9.5], 're_centered_position': [2.125, 10.75]},
    {'height': 1, 'width': 2, 'position': [5.5, 1.5], 're_centered_position': [6.5, 2]},
    {'height': 1, 'width': 2, 'position': [7.5, 1.5], 're_centered_position': [8.5, 2]},
    {'height': 1, 'width': 2, 'position': [9.5, 1.5], 're_centered_position': [10.5, 2]},
    {'height': 1, 'width': 2, 'position': [11.5, 1.5], 're_centered_position': [12.5, 2]},
    {'height': 1, 'width': 2, 'position': [13.5, 1.5], 're_centered_position': [14.5, 2]},
    {'height': 1, 'width': 2, 'position': [5.5, 5.5], 're_centered_position': [6.5, 6]},
    {'height': 1, 'width': 2, 'position': [7.5, 5.5], 're_centered_position': [8.5, 6]},
    {'height': 1, 'width': 2, 'position': [9.5, 5.5], 're_centered_position': [10.5, 6]},
    {'height': 1, 'width': 2, 'position': [11.5, 5.5], 're_centered_position': [12.5, 6]},
    {'height': 1, 'width': 2, 'position': [13.5, 5.5], 're_centered_position': [14.5, 6]},
    {'height': 1, 'width': 2, 'position': [5.5, 9.5], 're_centered_position': [6.5, 10]},
    {'height': 1, 'width': 2, 'position': [7.5, 9.5], 're_centered_position': [8.5, 10]},
    {'height': 1, 'width': 2, 'position': [9.5, 9.5], 're_centered_position': [10.5, 10]},
    {'height': 1, 'width': 2, 'position': [11.5, 9.5], 're_centered_position': [12.5, 10]},
    {'height': 1, 'width': 2, 'position': [13.5, 9.5], 're_centered_position': [14.5, 10]},
    {'height': 1, 'width': 2, 'position': [5.5, 13.5], 're_centered_position': [6.5, 14]},
    {'height': 1, 'width': 2, 'position': [7.5, 13.5], 're_centered_position': [8.5, 14]},
    {'height': 1, 'width': 2, 'position': [9.5, 13.5], 're_centered_position': [10.5, 14]},
    {'height': 1, 'width': 2, 'position': [11.5, 13.5], 're_centered_position': [12.5, 14]},
    {'height': 1, 'width': 2, 'position': [13.5, 13.5], 're_centered_position': [14.5, 14]},
    {'height': 1, 'width': 2, 'position': [5.5, 17.5], 're_centered_position': [6.5, 18]},
    {'height': 1, 'width': 2, 'position': [7.5, 17.5], 're_centered_position': [8.5, 18]},
    {'height': 1, 'width': 2, 'position': [9.5, 17.5], 're_centered_position': [10.5, 18]},
    {'height': 1, 'width': 2, 'position': [11.5, 17.5], 're_centered_position': [12.5, 18]},
    {'height': 1, 'width': 2, 'position': [13.5, 17.5], 're_centered_position': [14.5, 18]},
    {'height': 1, 'width': 2, 'position': [5.5, 21.5], 're_centered_position': [6.5, 22]},
    {'height': 1, 'width': 2, 'position': [7.5, 21.5], 're_centered_position': [8.5, 22]},
    {'height': 1, 'width': 2, 'position': [9.5, 21.5], 're_centered_position': [10.5, 22]},
    {'height': 1, 'width': 2, 'position': [11.5, 21.5], 're_centered_position': [12.5, 22]},
    {'height': 1, 'width': 2, 'position': [13.5, 21.5], 're_centered_position': [14.5, 22]},
    {'height': 6, 'width': 0.7, 'position': [1, 18.5], 're_centered_position': [1.35, 21.5]},
    {'height': 6, 'width': 0.7, 'position': [2, 18.5], 're_centered_position': [2.35, 21.5]},
    {'height': 0.8, 'width': 0.8, 'position': [3.5, 18.5], 're_centered_position': [4.15, 19.4]},
    {'height': 2.25, 'width': 1.5, 'position': [18.25, 4.75], 're_centered_position': [19.125, 5.875]},
    {'height': 2.25, 'width': 1.5, 'position': [18.25, 10.75], 're_centered_position': [19.125, 11.875]}
]


def update_position_to_center(obj_pose):
    global objs
    for obj in objs:
        # Compare current position with obj_pose
        if obj['position'] == obj_pose:
            # If they match, update position to re_centered_position
            obj_pose = obj['re_centered_position']
            break
    return obj_pose


class Agent:
    def __init__(self, socket_game, env):
        self.shopping_list = env['observation']['players'][0]['shopping_list']
        self.shopping_quant = env['observation']['players'][0]['list_quant']
        self.game = socket_game
        self.map_width = 20
        self.map_height = 25
        self.obs = env['observation']
        self.cart = None
        self.basket = None
        self.player = self.obs['players'][0]
        self.last_action = "NOP"
        self.current_direction = self.player['direction']
        self.size = [0.6, 0.4]

        logging.debug(f"Agent Initialized | Shopping List: {self.shopping_list} | Player Position: {self.player['position']}")

    def step(self, action):
        action = "0 " + action
        self.game.send(str.encode(action))
        output = recv_socket_data(self.game)

        if output:
            output = json.loads(output)
            self.obs = output['observation']
            self.player = self.obs['players'][0]
            self.last_action = action

            logging.debug(f"Action Performed: {action} | New Position: {self.player['position']}")
        return output

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def is_close_enough(self, current, goal, tolerance=1, is_item = True):
        if is_item is not None:
            tolerance = 0.6
            return (abs(current[0] - goal[0]) < tolerance - 0.15  and abs(current[1] - goal[1]) < tolerance +0.05 )

        else:
            return (abs(current[0] - goal[0]) < tolerance and abs(current[1] - goal[1]) < tolerance)

    def distance(self, a, b):
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def neighbors(self, point, goal, map_width, map_height, objs):
        step = 0.150
        directions = [(0, step), (step, 0), (0, -step), (-step, 0)]
        x, y = point
        results = []

        for dx, dy in directions:
            nx = round((x + dx) / 0.05) * 0.05 
            ny = round((y + dy) / 0.05) * 0.05  
            nx, ny = round(nx, 2), round(ny, 2)

            if 0 <= nx < map_width and 0 <= ny < map_height and all(
                self.collision(nx, ny, self.size[0], self.size[1], obj) for obj in objs
            ):
                results.append((nx, ny))

        results.sort(key=lambda n: self.heuristic(n, goal)) 
        logging.debug(f"Generated Neighbors for {point} (Sorted by Heuristic): {results}")
        return results

    def astar(self, start, goal, objs, map_width, map_height, is_item=True):
        x, y = goal
        goal = update_position_to_center([x, y])
        logging.debug(f"A* Search Started | Start: {start} | Goal: {goal}")

        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {}
        cost_so_far = {}
        start = tuple(start)  
        goal = tuple(goal)   
        came_from[start] = None  
        cost_so_far[start] = 0


        while not frontier.empty():
            _, current = frontier.get()
            current = tuple(current) 
            logging.debug(f"Exploring Node: {current}")

            if self.is_close_enough(current, goal, is_item=is_item):
                logging.debug(f"Goal Reached at {current}")
                break

            for next_node in self.neighbors(current, goal, map_width, map_height, objs):
                next_node = tuple(next_node) 
                new_cost = cost_so_far[current] + 0.15
                new_cost = round(new_cost / 0.05) * 0.05  
                new_cost = round(new_cost, 2)
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(next_node, goal)
                    frontier.put((priority, next_node))
                    came_from[next_node] = current
                    logging.debug(f"Added to Frontier: {next_node} (Cost: {new_cost}, Priority: {priority})")

        if self.is_close_enough(current, goal, is_item=is_item):
            path = []
            while current:
                path.append(current)
                current = came_from[current]
            path.reverse()
            logging.debug(f"Path Found: {path}")
            return path

        logging.warning(f"No Path Found from {start} to {goal}")
        return None

    def collision(self, x, y, width, height, obj):
        min_x, max_x = 2.5, 19.5
        min_y, max_y = 0.5, 24

        rectangle = {'northmost': y, 'southmost': y + height, 'westmost': x, 'eastmost': x + width}

        if not (min_x <= rectangle['westmost'] <= max_x and min_y <= rectangle['northmost'] <= max_y):
            logging.debug(f"Collision Detected: Out of Bounds ({x}, {y})")
            return False

        obj_box = {'northmost': obj['position'][1], 'southmost': obj['position'][1] + obj['height'],
                   'westmost': obj['position'][0], 'eastmost': obj['position'][0] + obj['width']}

        no_overlap = not (
            (obj_box['northmost'] <= rectangle['northmost'] <= obj_box['southmost'] or
             obj_box['northmost'] <= rectangle['southmost'] <= obj_box['southmost']) and
            (obj_box['westmost'] <= rectangle['westmost'] <= obj_box['eastmost'] or
             obj_box['westmost'] <= rectangle['eastmost'] <= obj_box['eastmost'])
        )

        if not no_overlap:
            logging.debug(f"Collision Detected with Object at {obj['position']}")
        return no_overlap
