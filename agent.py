import json
import math
from utils import recv_socket_data

def navigate_json(json_obj, keys):
    current = json_obj
    for key in keys:
        current = current[key]
    return current


class Agent:
    def __init__(self, sock_game, curr_player):
        self.sock_game = sock_game
        self.curr_player = curr_player

    def send_action(self, action):
        action = str(self.curr_player) + " " + action
        print("Sending action: ", action)
        self.sock_game.send(str.encode(action))  # send action to env

        output = recv_socket_data(self.sock_game)  # get observation from env
        self.curr_state = json.loads(output)
        return self.curr_state

    def turn_to(self, target):
        # target is in the form of an array of keys in json
        player_direction = self.curr_state["direction"]
        target_direction = navigate_json(self.curr_state, [target])["direction"]
        action = "NOP"

        if (player_direction != target_direction):
            match target_direction:
                case 0:
                    action = "NORTH"
                case 1:
                    action = "EAST"
                case 2:
                    action = "WEST"
                case 3:
                    action = "SOUTH"

            print(f"Turning from {player_direction} to {target_direction} using action {action}")
            self.curr_state = self.send_action(action)

        print(f"Turned to target direction: {target_direction}")            
                
    def move_to(self, target_position):
        # target is in the form of an array of keys in json

        player_position = self.curr_state["position"]

        while player_position != target_position:
            delta_x = target_position[0] - player_position[0]
            delta_y = target_position[1] - player_position[1]
            action = "NOP"

            # Determine the next action
            if abs(delta_x) > abs(delta_y):  # Move horizontally
                if delta_x > 0:
                    action = "EAST"
                else:
                    action = "WEST"
            else:  # Move vertically
                if delta_y > 0:
                    action = "NORTH"
                else:
                    action = "SOUTH"

            # Send the action to the environment
            print(f"Moving from {player_position} towards {target_position} using action {action}")
            self.curr_state = self.send_action(action)

            # Update the player's current position
            player_position = self.curr_state["position"]

        print(f"Arrived at target position: {target_position}")

    def move_to(self, target):
        # target is in the form of an array of keys in json

        player_position = self.curr_state["position"]
        target_position = navigate_json(self.curr_state, [target])["position"]


        while player_position != target_position:
            delta_x = target_position[0] - player_position[0]
            delta_y = target_position[1] - player_position[1]
            action = "NOP"

            # Determine the next action
            if abs(delta_x) > abs(delta_y):  # Move horizontally
                if delta_x > 0:
                    action = "EAST"
                else:
                    action = "WEST"
            else:  # Move vertically
                if delta_y > 0:
                    action = "NORTH"
                else:
                    action = "SOUTH"

            # Send the action to the environment
            print(f"Moving from {player_position} towards {target_position} using action {action}")
            self.curr_state = self.send_action(action)

            # Update the player's current position
            player_position = self.curr_state["position"]

        print(f"Arrived at target position: {target_position}")

    def interact(self):
        self.send_action("INTERACT")
        self.send_action("INTERACT")

    def get_curr_cart(self):
        # Returns whether or not you have a cart
        return self.curr_state["curr_cart"]
    
    def get_nearest_cart(self):
        player_position = self.curr_state["position"]
        carts = self.check_carts()

        if not carts:
            print("No carts available.")
            return None

        nearest_cart_index = -1
        min_distance = float('inf')

        for i, cart in enumerate(carts):
            cart_position = cart["position"]
            distance = math.sqrt(
                (cart_position[0] - player_position[0]) ** 2 +
                (cart_position[1] - player_position[1]) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                nearest_cart_index = i

        return nearest_cart_index

    def check_carts(self):
        # Returns information about every cart on the map
        return self.curr_state["carts"]
    
    def find_carts_with(self, items):
        # Returns information about carts with specific items
        carts = self.check_carts()
        matching_carts = []

        for cart in carts:
            if set(items).issubset(set(cart.get("contents", []))):
                matching_carts.append(cart)
        return matching_carts

    def toggle_cart(self):
        self.send_action("TOGGLE_CART")

    def grab_cart(self, cart):
        cart_position = cart["position"]
        cart_direction = cart["direction"]

        self.move_to(target_position=cart_position)
        self.turn_to(target_position=cart_direction)

        self.toggle_cart()
        print(f"Grabbing cart at target position: {cart_position}")
        
    def grab_cart_from_return(self):
        cart_returns_position = ["cartReturns", 0]

        self.move_to(target_position=cart_returns_position)
        self.turn_to(2)

        self.interact()
        print(f"Grabbing cart from cart returns")

    def load_cart(self, cart):
        cart_position = cart["position"]
        cart_direction = cart["direction"]

        self.move_to(target_position=cart_position)
        self.turn_to(cart_direction)

        self.send_action("INTERACT")
        print(f"Putting item in cart at target position: {cart_position}")

    def retrieve_item(self, item):
        if (self.get_curr_cart() != -1):
            self.toggle_cart()

        item_position, item_direction = self.find_item(item)
        self.move_to(target_position=item_position)
        self.turn_to(item_direction)
        self.grab_item()

    def grab_item(self):
        self.interact()
        self.load_cart()

    def find_item(self, item):
        player_position = self.curr_state["position"]

        shelves = self.curr_state["shelves"]
        for shelf in shelves:
            if shelf["food"] == item:
                shelf_position = shelf["position"]
                
                # Calculate the relative direction
                delta_x = shelf_position[0] - player_position[0]
                delta_y = shelf_position[1] - player_position[1]

                angle = math.degrees(math.atan2(delta_y, delta_x))
                if angle < 0:
                    angle += 360  # Normalize angle to [0, 360)

                # Map angle to cardinal directions
                if 45 <= angle < 135:
                    direction = 0
                elif 135 <= angle < 225:
                    direction = 1
                elif 225 <= angle < 315:
                    direction = 2
                else:
                    direction = 3

                print(f"Item '{item}' found at position {shelf_position}. Direction: {direction}")
                return shelf_position, direction

        print(f"Item '{item}' not found in any shelf.")
        return None

    def check_quest_requirements(self, quest):
        print(f"[Quest: {quest.name}] Requirements: '{quest.requirements}'.")
        return quest.requirements
    
    def check_quest_requirements_against_bag(self, quest):
        requirements = self.check_quest_requirements(quest)
        bagged_items = dict(zip(self.curr_state["bagged_items"], self.curr_state["bagged_quant"]))

        for required_item, required_quantity in requirements.items():
            bagged_quantity = 0
            if (required_item == "any"):
                bagged_quantity = sum(bagged_items.values())
            else:
                bagged_quantity = bagged_items.get(required_item, 0)
            if bagged_quantity < required_quantity:
                print(f"Requirement for '{required_item}' not met! Bagged; {bagged_quantity}. Required: {required_quantity}")
                return False
            
        print("All requirements met!")
        return True
    
    def check_quest_requirements_against_curr_cart(self, quest):
        requirements = self.check_quest_requirements(quest)
        curr_cart = self.get_curr_cart()
        cart_items = dict(zip(self.curr_state["carts"][curr_cart]["contents"], self.curr_state["carts"][curr_cart]["contents_quant"]))

        for required_item, required_quantity in requirements.items():
            cart_quantity = 0
            if (required_item == "any"):
                cart_quantity = sum(cart_items.values())
            else:
                cart_quantity = cart_items.get(required_item, 0)
            if cart_quantity < required_quantity:
                print(f"Requirement for '{required_item}' not met! Bagged; {cart_quantity}. Required: {required_quantity}")
                return False
            
        print("All requirements met!")
        return True

    def check_hand(self):
        return self.curr_state['holding_food']

    def leave_store():
        print()

    def purchase_items(self, quest):
        requirements = self.check_quest_requirements(quest)
        if (len(self.check_carts()) == 0):
            self.grab_cart_from_return()
        else:
            self.grab_cart(self.get_nearest_cart())

        for required_item, required_quantity in requirements:
            for _ in range(required_quantity):
                self.retrieve_item(required_item)

        if (self.check_quest_requirements_against_curr_cart(quest)):
            self.checkout(quest)

    def checkout(self, quest):
        if (self.check_quest_requirements_against_bag(quest)):
            self.leave_store()

    
    def complete_quest(self, quest):
        if (self.check_quest_requirements_against_bag(quest)):
            self.leave_store()
        else:
            self.purchase_items(quest)
    