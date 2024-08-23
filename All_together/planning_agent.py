import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import json  # Import json for dictionary serialization

from constants import *
from PIL import Image


class PlanningAgent:
    '''
    Path planning agent for fast navigation
    '''
    def __init__(self, name, target, playerNum):
        self.name = name 
        self.target = target
        self.action_directions = [[0, -1], [0, 1], [1, 0], [-1, 0]] 
        self.action_commands = ['NORTH', 'SOUTH', 'EAST', 'WEST']
        self.map = None
        self.playerNum = playerNum 
        self.granularity = 0.1
    
    #Map used for navigation, composed of horizonal and vertical filled blocks with buffer
    def build_map(self):
        self.map = np.zeros((int(max_x/self.granularity), int(max_y/self.granularity)))

        # set up horizontal blocks
        for block in horizontal_blocks:
            # print(block)
            # print(block[1])
            x1, y1 = int(block[0][0]/self.granularity), int(block[0][1]/self.granularity)
            x2, y2 = int(block[1][0]/self.granularity), int(block[1][1]/self.granularity)
            assert y1 == y2
            # if block[0][1] == 16.8:
            #     for i in range(x1, x2):
            #         # print(i, y1)
            self.map[x1:x2, y1] = 99999999

        # set up vertical blocks
        for block in vertical_blocks:
            x1, y1 = int(block[0][0]/self.granularity), int(block[0][1]/self.granularity)
            x2, y2 = int(block[1][0]/self.granularity), int(block[1][1]/self.granularity) 
            assert x1 == x2
            self.map[x1, y1:y2] = 99999999 
        
        start = cart_obj_pos_dict[self.target]
        start_x, start_y = int(start[0]/self.granularity), int(start[1]/self.granularity) 
        self.map[start_x, start_y] = 0
        queue = [(start_x, start_y, 0)] 

        #BFS over map to map directions to action
        while len(queue) != 0:
            x, y, d = queue.pop(0) 
            if self.map[x, y] != 0:
                continue
            self.map[x, y] = d
            for direction in self.action_directions:
                x_, y_ = x + direction[0], y + direction[1]
                if x_ >= 0 and x_ < self.map.shape[0] and y_ >= 0 and y_ < self.map.shape[1]:
                    if self.map[x_, y_] == 0:
                        queue.append((x_, y_, d + 1)) 
        
        for x in range(self.map.shape[0]):
            for y in range(self.map.shape[1]):
                if self.map[x, y] == 0 and (x, y) != (start_x, start_y):
                    self.map[x, y] = 99999999  

    def learning(self, action, rwd, state, next_state):
        pass

    def save_qtables(self):
        pass 

    def load_qtables(self):
        self.build_map() 

    #Temporary overlayed map to get correct cart and baskets from
    #different options provided
    def _get_temporary_map(self, state, radius=5):
        # return self.map
        players_info = state['observation']['players']
        carts_info = state['observation']['carts'] 
        baskets_info = state['observation']['baskets'] 
        my_basket_id = 0
        for i, basket in enumerate(baskets_info):
            if basket['owner'] == self.playerNum:
                my_basket_id = i
                break

        my_cart_id = players_info[self.playerNum]['curr_cart'] 
        # print(state)
        for i, cart in enumerate(state['observation']['carts']):
            if cart['owner'] == self.playerNum:
                my_basket_id = i 
                break
        # my_basket_id = players_info[self.playerNum]['curr_basket']

        #iterate over other players in map to build out online planning
        temp_map = self.map.copy() 
        for id, player in enumerate(players_info):
            if id == self.playerNum:
                continue
            position = player['position']
            x, y = int(position[0]/0.2), int(position[1]/0.2)
            for i in range(-radius, radius+1):
                for j in range(-radius, radius+1):
                    if x + i >= 0 and x + i < temp_map.shape[0] and y + j >= 0 and y + j < temp_map.shape[1]:
                        temp_map[x+i, y+j] = 99999999
            # temp_map[x, y] = 99999999 
        for id, cart in enumerate(carts_info):
            if id == my_cart_id:
                continue
            position = cart['position']
            x, y = int(position[0]/0.2), int(position[1]/0.2)
            for i in range(-radius, radius+1):
                for j in range(-radius, radius+1):
                    if x + i >= 0 and x + i < temp_map.shape[0] and y + j >= 0 and y + j < temp_map.shape[1]:
                        temp_map[x+i, y+j] = 99999999
            # temp_map[x, y] = 99999999 

        for id, basket in enumerate(baskets_info):
            if id == my_basket_id:
                continue
            position = basket['position']
            x, y = int(position[0]/0.2), int(position[1]/0.2)
            for i in range(-radius, radius+1):
                for j in range(-radius, radius+1):
                    if x + i >= 0 and x + i < temp_map.shape[0] and y + j >= 0 and y + j < temp_map.shape[1]:
                        temp_map[x+i, y+j] = 99999999
            # temp_map[x, y] = 99999999 

        return temp_map

    #Choose action corresponding to min value of path distance
    #If multiple values of same weight then choose randomly
    def choose_action(self, state): 
        self.visualize()
        # print(state['observation']['players'][self.playerNum].keys())
        player_info = state['observation']['players'][self.playerNum]
        position = player_info['position'] 
        curr_map = self._get_temporary_map(state)
        cur_position = [int(position[0] / self.granularity), int(position[1] / self.granularity)] 
        values = [0, 0, 0, 0] 

        #Find best position from stored temporary map
        for i, d in enumerate(self.action_directions):
            x, y = cur_position[0] + d[0], cur_position[1] + d[1]
            values[i] = curr_map[x, y] 
        # action = np.argmin(values) 
        min_value = np.min(values)
        candidates = [i for i in range(4) if values[i] == min_value] 
        action = np.random.choice(candidates)
        # print(action, '  ', values[action])
        #Eliminate high value actions
        if values[action] == 99999999:
            return np.random.randint(4), False
        return action, values[action] < 2
    
    #Visualize the map into a cost map
    def visualize(self):
        map = self.map.copy() 
        # print(map.shape)
        for i in range(len(map)):
            for j in range(len(map[i])):
                if map[i][j] > 99999:
                    map[i][j] = 0 
                else:
                    map[i][j] = 255

        map = map.T
        image = Image.fromarray(map.astype(np.uint8)) 
        image.save('slam.jpg')
