import json
import random
import socket

from env import SupermarketEnv
from utils import recv_socket_data
import followplan   
import preliminary_path

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
    "prepared food": [18, 5],
    "fresh fish": [17.0, 15.0],
    "checkout": [4.0, 11.5],
    "exit": [-0.5, 15.6],
    "corner_1": [18, 2],
    "corner_2": [18, 22]
}

HOST = '127.0.0.1'
PORT = 9000
sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_game.connect((HOST, PORT))
sock_game.send(str.encode("0 RESET"))  # reset the game

print("Which player number are you?")
playernumber = int(input())
output = recv_socket_data(sock_game)
game_state = json.loads(output)
print("got observations for the first time")

""" steps = 0
while steps < 10: 
    action = "0 " + "SOUTH"
    print("Sending action: ", action)
    sock_game.send(str.encode(action))  # send action to env
    output = recv_socket_data(sock_game)  # get observation from env
    output = json.loads(output)
    steps += 1 """


shopping_list = game_state['observation']['players'][playernumber]['shopping_list']
for i in range(len(shopping_list)):
    if shopping_list[i] == "prepared foods":
        print("removing prepared foods")
        shopping_list.remove('prepared foods')
        break

shopping_quant = game_state['observation']['players'][playernumber]['list_quant']
player = preliminary_path.PathPlanner()
print("Created Preliminary Path")
itemcount = sum(shopping_quant)

if itemcount > 6:
    print("More than 6, get a cart")
    state = followplan.GetCurrentState(game_state, playernumber)
    while state.find("cart") == -1:
        path = player.grab_cart_or_basket(game_state, playernumber, kind="cart")
        print("got the path to cart")
        #print("Path: ", path)
        results = followplan.ExecutePlanToItem(path, sock_game, playernumber, goal="cart")
        ## Updating game_state from environment
        sock_game.send(str.encode("0 NOP"))
        print("sent NOP to environment")
        output = recv_socket_data(sock_game)
        print("got output from environment")
        game_state = json.loads(output) # get new state
        state = followplan.GetCurrentState(game_state, playernumber)
        print("state-find: ", state.find("cart"))

    has_cart = True
    print("\n\n\n\n\n Got the cart")
else:
    print("less than 6, get a basket")
    state = followplan.GetCurrentState(game_state, playernumber)
    print("state: ", state)
    while state.find("basket") == -1:
        path = player.grab_cart_or_basket(game_state, playernumber, kind="basket")
        print("got the path to basket")
        #print("Path: ", path)
        results = followplan.ExecutePlanToItem(path, sock_game, playernumber, goal="basket")


        ## Updating game_state from environment
        sock_game.send(str.encode("0 NOP"))
        output = recv_socket_data(sock_game)
        game_state = json.loads(output) # get new state
        state = followplan.GetCurrentState(game_state, playernumber)
        print("state-find: ", state.find("basket"))


    has_cart = False
    print("\n\n\n\n\n Got the basket")
## end of the "do once" section

# get all the items on the shopping list
while len(shopping_list) > 0:
    print("Shopping list: ", shopping_list)
    print("Shopping quant: ", shopping_quant)


    ## Updating game_state from environment
    sock_game.send(str.encode("0 NOP"))
    print("sent NOP to environment")
    output = recv_socket_data(sock_game)
    print("got output from environment")
    game_state = json.loads(output) # get new state


    print("about to get the next shopping item")
    nextitem = followplan.get_next_shopping_item(game_state, playernumber, shopping_list, shopping_quant)
    print("got the next shopping item")
    nextitemPos = target_locations[nextitem[0]]
    path = player.get_path(game_state, nextitemPos, has_cart, playernumber)
    # now take the path and excute it
    results = followplan.ExecutePlanToItem(path, sock_game, playernumber)
    if results == "ERROR":
        print("Error")
        # make a new plan, this one failed
    else:
        print("Got the item")
        # make a new plan, but first remove the item we already got from the shopping list
        print("shopping list before removal: ", shopping_list)
        print("next item is ", nextitem)
        shopping_list.remove(nextitem[0])
        shopping_quant.pop(0)

# update game state so we can plan to the checkout
sock_game.send(str.encode("0 NOP"))
output = recv_socket_data(sock_game)
game_state = json.loads(output) # get new state   
path = player.checkout(game_state, playernumber)
# go to the checkout

status = followplan.ExecutePlanToItem(path, sock_game, playernumber)
print("checkout status is ", status)
while status != "SUCCESS":
    path = player.checkout(game_state)
    status = followplan.ExecutePlanToItem(path, sock_game, playernumber)
    print("checkout status is ", status)
print("leaving the store")
# update game state so we can plan to the exit
sock_game.send(str.encode("0 NOP"))
output = recv_socket_data(sock_game)
game_state = json.loads(output) # get new state   
player.leave_store(game_state, playernumber)

sock_game.close()
     
