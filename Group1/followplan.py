# Author: Mavis, Kat, Harsh, Ju-Hung, Luoyou

import json
import random
import socket
import time
from utils import recv_socket_data
#from astar_path_planner import *
from navigation_utils import *

target_locations = {
    "entrance": [0.15, 15],
    "counter": [3, 12],
    "cart": [1, 17.5],
    "milk": [5.5, 3.5],
    "chocolate milk": [9.5, 3.5],
    "strawberry milk": [13.5, 3.5],
    "apples": [5.5, 7.5],
    "oranges": [7.5, 7.5],
    "banana": [9.5, 7.5],
    "strawberry": [11.5, 7.5],
    "raspberry": [13.5, 7.5],
    "sausage": [5.5, 11.5],
    "steak": [7.5, 11.5],
    "chicken": [11.5, 11.5],
    "ham": [13.5, 11.5],
    "brie cheese": [5.5, 15.5],
    "swiss cheese": [7.5, 15.5],
    "cheese wheel": [9.5, 15.5],
    "garlic": [5.5, 19.5],
    "leek": [7.5, 19.5],
    "red bell pepper": [9.5, 19.5],
    "carrot": [11.5, 19.5],
    "lettuce": [13.5, 19.5],
    "avocado": [5.5, 23.5],
    "broccoli": [7.5, 23.5],
    "cucumber": [9.5, 23.5],
    "yellow bell pepper": [11.5, 23.5],
    "onion": [13.5, 23.5],
    "prepared foods": [18, 5],
    "fresh fish": [17.0, 15.0],
    "checkout": [4.0, 11.5],
    "exit": [-0.5, 15.6],
    "corner_1": [18, 2],
    "corner_2": [18, 22]
}

def get_item_location(item):
    item_pos = target_locations[item]
    if item != 'prepared foods' and item != 'fresh fish':
        item_pos = target_locations[item]
    else:
        if item == 'prepared foods':
            item_pos = [18.25, 4.75]
        else:
            item_pos = [18.25, 10.75]
    if item == 'milk' or item == 'chocolate milk' or item == 'strawberry milk':
        y_offset = 3
    else:
        y_offset = 0

    item_location = [item_pos[0] + offset, item_pos[1] + y_offset]
    return item_location

def wait_in_the_corner(player, player_number):
    # takes in Agent object
    # get current location
    output = recv_socket_data(player.socket_game)  # assuming `socket_game` is the correct variable name
    state = json.loads(output)
    for player in state["observation"]["players"]:
        if player['index'] == player_number:
            location = player["position"]
            break

    # use astar to plan the path (trail ver, the agent only goes to top right corner)
    path = player.astar((location[0], location[1]),
                        (target_locations["corner_1"][0], target_locations["corner_1"][1]), objs, 20, 25)
    player.perform_actions(player.from_path_to_actions(path))

    # wait 5 sec
    time.sleep(5)

    return None

def euclidean_distance(pos1, pos2):
    # Calculate Euclidean distance between two points
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5


def get_next_shopping_item(game_state, playernumber, shopping_list, shopping_quants):
    for player in game_state["observation"]["players"]:
        if player['index'] == playernumber:
            user_location = player['position']

    quant_dict = dict(zip(shopping_list, shopping_quants))

    curr_min_distance = 999999999
    closest_item = None

    for item in shopping_list:
        coord = target_locations[item]
        distance = euclidean_distance(user_location, coord)
        if distance < curr_min_distance:
            curr_min_distance = distance
            closest_item = item
    
    # return closest_item
    return (closest_item, quant_dict[closest_item])



def GetCurrentState(game_state, playernumber): 
##  example state {'NORTH,basket(4.05, 10.65)': 'NOOP', ...}
## 0: North 1: south 2: east 3: west

    # get the current state of the environment
    state = ""
    directions = ['NORTH', 'SOUTH', 'EAST', 'WEST']

    for player in game_state["observation"]["players"]:
        if player['index'] == playernumber:
            directionfacing = player["direction"]
            ##print("directionfacing: ", directionfacing)
            direction = directions[directionfacing]  
            ##print("direction: ", direction) 
            state = state + direction + ","

    if game_state["observation"]['baskets'] != []:
        for basket in list(game_state["observation"]['baskets']):
            if basket['owner'] == playernumber:
                state = state + "basket,"       
    if game_state["observation"]['players'][playernumber]["curr_cart"] >= 0:
        state = state + "cart,"
    for key in game_state["observation"]: 
        for key2 in game_state["observation"][key]: 
            if key == "players":
                for thisplayer in list(game_state["observation"][key]):
                    ##print("thisplayer: ", thisplayer)
                    ##print(thisplayer['index'])
                    if thisplayer['index'] == playernumber:
                        ##print("found player")
                        currentposition = round(key2["position"][0],3), round(key2["position"][1],3) # round to 3 decimal places
                        currentposition = str(currentposition)
                        currentposition = currentposition.replace("[", "(")
                        currentposition = currentposition.replace("]", ")")
                        ##print("currentposition: ", currentposition)
                        state = state + currentposition


    ##print("state: ", state)                
    return state

def send_action(action, sock_game, playernumber):
    formataction = str(playernumber) + " " + action
    ##print("formataction: ", formataction)
    sock_game.send(str.encode(formataction))  # send action to env
    ##print("sent action to environment")
    output = recv_socket_data(sock_game)
    game_state = json.loads(output) # get new state
    state = GetCurrentState(game_state, playernumber)
    return state

def ExecutePlanToItem(path, sock_game, playernumber, goal=""): 
    # the path is a dictionary of states and actions
    # get the current state from the environment
    # find out if the current state is any of the states in the path
    # if so, execute the action
    # if not, return an error
    pollingcounter = 0
    results = ""
    endpath = False
    while results != "SUCCESS":
        ##print("path is ", path)
        sock_game.send(str.encode("0 NOP"))
        ##print("sent NOP to environment in ExecutePlanToItem")
        output = recv_socket_data(sock_game)
        ##print("got output from environment")
        game_state = json.loads(output) # get new state
        ##print("got formatted observation back from environment in ExecutePlanToItem")
        ##print("observation: ", observation)
        state = GetCurrentState(game_state, playernumber) 
        polllength = 3

        for key in path:
            if pollingcounter > polllength:
                ##print("checking path for blockage")
                pollingcounter = 0 # reset the counter
                isblocked = path_blocked(playernumber, path, game_state)
                if isblocked == True:
                    #print("path is blocked")
                    return "ERROR"

            ##print("the key we are checking is " + key)
            ##print("the action for the key is " + str(path[key]))
            if key.find(state) != -1: # if the state is in the path (usually it will be the whole path, 
                                        # but not when END is included in the action)
                ##print("matched key.  checking for end of path")
                if key.find("END") != -1: # if the action includes "END" then we are at the end of path
                    ##print("End of path")
                    endpath = True
                ##print("Checking against norms")
                
                # set the action to what is specified in the path and then check if it is allowed
                action = path[key]
                ##print("action to be checked:", action)
                actionok, action= checknorms(action)
                if actionok == True:
                    ## actually take the action in the environment
                    ##print("Sending action: ", action)
                    state = send_action(action, sock_game, playernumber)
                    # do not remove the state from the path in case we return to it, e.g. in the stochastic action scenario
                    pollingcounter = pollingcounter + 1 # increment the stepcount
                    if endpath == True:
                        ##print("End of path actions complete, checking for goal ", goal)
                        if goal == "cart" or goal == "basket":
                            if state.find(goal) != -1 or state.find("cart") != -1:
                                #print("cart/basket acquired")
                                results = "SUCCESS"
                            else:
                                #print("cart/basket not acquired")
                                while state.find(goal) == -1 and state.find("cart") == -1:
                                    #print("cart/basket not acquired, trying again")
                                    action = "INTERACT"
                                    state = send_action(action, sock_game, playernumber)
                                    #print(state)


                        else: #if we were not looking for a cart or a basket, just assume for now we got it.
                            # this could be replaced with a real check for the item we were supposed to get
                            
                            results = "SUCCESS"
                        return results
                else:
                    print("Action not allowed")
                    return "ERROR"
        # if it never finds they key in the path, something is wrong -- re-plan    
        print("State ", state, " not in path")
        return "ERROR"
        
def checknorms(action):
    # use norm.py to check if the action is allowed
    # this is hard, for now

    if action == False:
        action = "INTERACT"
    return True, action
    
    