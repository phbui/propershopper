import ujson as json
import random
import socket
import gymnasium as gym
from env import SupermarketEnv
from utils import recv_socket_data

# [16.30, 7.80], [16.30, 3.75], 
target_coordinates = {"carts": [2, [1, 18.00], [2,18.00]], "baskets": [1, [3.5, 18.00]], "fresh fish": [1, [16.30, 11.70]], "prepared foods": [1, [16.30, 7.80]],"checkout counter": [2, [3.60, 12.15], [3.60, 7.35]],"milk": [1, [7.35, 3.75]], "chocolate milk": [1, [11.25, 3.75]], "strawberry milk": [1, [14.25, 3.75]], "raspberry": [2, [14.40, 3.75], [14.40, 7.80]], "strawberry": [2, [12.15, 3.75], [12.15, 7.80]], "banana": [2, [10.20, 3.75], [10.20, 7.80]], "oranges": [2, [8.25, 3.75], [8.25, 7.80]], "apples": [2, [6.30, 3.75], [6.30, 7.80]], "ham": [2, [14.40, 11.70], [14.40, 7.80]], "chicken": [2, [12.15, 11.70], [12.15, 7.80]], "steak": [2, [9.20, 11.70], [9.20, 7.80]], "sausage": [2, [6.30, 11.70], [6.30, 7.80]], "brie cheese": [2, [6.30, 11.70], [6.30, 15.60]], "swiss cheese": [2, [8.25, 11.70], [8.25, 15.60]], "cheese wheel": [2, [12.15, 11.70], [12.15, 15.60]], "lettuce": [2, [14.40, 15.60], [14.40, 19.65]], "carrot": [2, [12.15, 15.60], [12.15, 19.65]], "red bell pepper": [2, [10.20, 15.60], [10.20, 19.65]], "leek": [2, [8.25, 15.60], [8.25, 19.65]], "garlic": [2, [6.30, 15.60], [6.30, 19.65]], "onion": [1, [14.40, 19.65]], "yellow bell pepper": [1, [12.15, 19.65]], "cucumber": [1, [10.20, 19.65]], "broccoli": [1, [8.25, 19.65]], "avocado": [1, [6.30, 19.65]], "exit": [2, [0.60, 7.20], [0.60, 3.30]]}
# ADD THE COUNTERS
# "fresh fish": [1, [17.40, 13.05]], "prepared foods": [1, [17.40, 7.05]]
# "fresh fish": [2, [16.60, 11.70], [16.60, 15.6]], "prepared foods": [2, [17.40, 3.75], [17.40, 7.80]]
# shopping_list = ['milk', 'cucumber', 'red bell pepper', 'onion', 'avocado', 'cheese wheel', 'brie cheese', 'steak', 'chicken', 'prepared foods', 'milk', 'strawberry milk', 'chocolate milk', 'fresh fish', 'prepared foods']
# shopping_list = ['leek','brie cheese', 'steak', 'milk']
starting_location = [1, 15.3]

# NEW ADVANCED SEQUENCER
def sequenceInitialize(shopping_list, starting_location):
    # There are 6 isles through which we can walk. The bottom one is useless, as we can get any items from the bottom shelf from the isle above it. Therefore, we will work with 5 isles, and 6 shelves bordering them.
    shelf_data = [0, 0, 0, 0, 0, 0]
    i = 0
    # Putting each item in their shelf rows
    while i < len(shopping_list):
        item = shopping_list[i]
        item_coordinates = target_coordinates[item]
        if item_coordinates[0] == 1:
            item_y = item_coordinates[1][1]
            # print(item_y)
        else:
            item_y = round((item_coordinates[1][1] + item_coordinates[2][1]) / 2, 3)
            # print(item_y)
        # The 5 shelf y values from bottom to top are 19.65, 17.625, 13.65, 9.75, 5.775, and 3.75
        shelf_y = [19.65, 17.625, 13.65, 9.75, 5.775, 3.75]
        j = 0
        while j < len(shelf_y):
            if item_y == shelf_y[j]:
                shelf_data[j] += 1
                # print("detecting "+str(item))
            j += 1
        i += 1
    # print(shelf_data)
    # print("")
    # print("")
    # Shelves are now populated. We need to determine which isles we need to walk through.
    isle_data = [False, False, False, False, False]
    k = 0
    while k < len(isle_data):
        if shelf_data[k] > 0:
            isle_data[k] = True
            shelf_data[k] = 0
            shelf_data[k+1] = 0
        else:
            if shelf_data[k+1] > 0 and k == len(isle_data) - 1:
                isle_data[k] = True
                shelf_data[k+1] = 0
        k += 1
    # print(isle_data)

    # Now we know which isles we need to walk through. We just need to choose the right coordinates for each item to walk through the right isles
    target_list = []
    reordered_shopping_list = []
    isle_item_y = [19.65, 15.6, 11.7, 7.8, 3.75]
    l = 0
    while l < len(isle_item_y):
        # print(l)
        if isle_data[l] == True:
            m = 0
            while m < len(shopping_list):
                item = shopping_list[m]
                item_info = target_coordinates[item]
                # print(item)
                # print(item_info)
                # print(shopping_list)
                if item_info[0] == 1:
                    if item_info[1][1] == isle_item_y[l]:
                        target_list.append(item_info[1])
                        reordered_shopping_list.append(item)
                        shopping_list.remove(item)
                    elif item == "fresh fish":
                        target_list.append(item_info[1])
                        reordered_shopping_list.append(item)
                        shopping_list.remove(item)
                    elif item == "prepared foods":
                        target_list.append(item_info[1])
                        reordered_shopping_list.append(item)
                        shopping_list.remove(item)
                    else:
                        m += 1
                else:
                    if item_info[1][1] == isle_item_y[l]:
                        target_list.append(item_info[1])
                        reordered_shopping_list.append(item)
                        shopping_list.remove(item)   
                    elif item_info[2][1] == isle_item_y[l]:
                        target_list.append(item_info[2])
                        reordered_shopping_list.append(item)
                        shopping_list.remove(item)
                    else:
                        m += 1
        l += 1
    
    # Now to organize each isle to be most efficient in the x-axis
    verifiedAscending = False
    while verifiedAscending == False:
        prev_x = starting_location[0]
        verifiedAscending = True
        n = 0
        while n < len(reordered_shopping_list)-1:
            # If same y value and the distance from current x is decreasing, swap the values
            if target_list[n][1] == target_list[n+1][1] and abs(target_list[n][0] - prev_x) > abs(target_list[n+1][0] - prev_x):
                temp_target = target_list[n+1]
                temp_item = reordered_shopping_list[n+1]
                target_list[n+1] = target_list[n]
                reordered_shopping_list[n+1] = reordered_shopping_list[n]
                target_list[n] = temp_target
                reordered_shopping_list[n] = temp_item
                verifiedAscending = False
            if target_list[n][1] != target_list[n+1][1]:
                if target_list[n][0] > 10.2:
                    prev_x = 16.05
                else:
                    prev_x = 4.20
            n += 1
    return target_list, reordered_shopping_list

def checkForReorder(position, target_list, listOfTempObstacles):
    target = target_list[0]
    reorder = False
    # If agent is within 5 units of target, check to see if any temporary obstacles are occupying the target coordinates (within 1 unit). If so, move on to next target by moving current target to end of list
    if abs(position[0] - target[0]) < 5 and abs(position[1] - target[1]) < 5:
        for obstacle in listOfTempObstacles:
            if abs(obstacle[0] - target[0]) < 1 and abs(obstacle[1] - target[1]) < 1:
                reorder = True
    return reorder

def sequenceReorder(target_list, shopping_list, reorder):
    # If the command to reorder is given, then the first index of target_list and shopping_list are moved to the end, and the agent skips the target and goes on, then comes back later
    if reorder == True:
        target_list.append(target_list[0])
        shopping_list.append(shopping_list[0])
        target_list = target_list[1:]
        shopping_list = shopping_list[1:]

    return target_list, shopping_list