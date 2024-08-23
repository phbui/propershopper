# Author: Mavis, Kat, Harsh, Ju-Hung, Luoyou


def point_in_object(point, obj):
    """
    Check if a point is within the boundary of an object.

    Parameters:
        point (tuple): The (x, y) coordinates of the point to check.
        obj (dict): An object with 'position', 'width', and 'height' indicating its boundary.

    Returns:
        bool: Returns True if the point is inside the object, False otherwise.
    """
    x, y = point
    obj_left = obj['position'][0]
    obj_right = obj['position'][0] + obj['width']
    obj_top = obj['position'][1]
    obj_bottom = obj['position'][1] + obj['height']
    if obj_left <= x <= obj_right and obj_top <= y <= obj_bottom:
        return True

    return False


def path_blocked(player_id, path, game_state):
    """
    Determines if a given path is blocked by any other players or carts.

    Args:
        player_id (int): ID of the player whose path is being checked.
        path (list of tuples): The path the player intends to take, as a list of (x, y) coordinates.
        state (dict): The current game state, including positions of all players and carts.

    Returns:
        bool: True if path is blocked, False otherwise.
    """
    players = game_state['observation']['players']
    carts = game_state['observation']['carts']
    player = players[player_id]
    isHoldingCart = player['curr_cart'] != -1

    for point in path:
        # Check if point is inside any other players
        for player in players:
            if player['index'] != player_id:  # Ignore self
                if point_in_object(point, player):
                    return True

        # Check if point is inside any carts
        for cart in carts:
            if cart["owner"] == player_id and isHoldingCart:
                continue  # Skip the cart being held by the player
            if point_in_object(point, cart):
                return True

    return False


def check_in_front(player_id, state, distance):
    """
    Check if there's any obstacle directly in front of the player within a specified distance
    by sampling points at every 0.1 units along the direction the player is facing.

    Args:
        player_id (int): ID of the player to check.
        state (dict): Current game state.
        distance (float): Distance to check in front of the player.

    Returns:
        bool: True if there's an obstacle in front, False otherwise.
    """
    players = state['observation']['players']
    carts = state['observation']['carts']
    player = players[player_id]
    isHoldingCart = player['curr_cart'] != -1

    # Player properties
    x, y = player['position']
    x += player['width'] / 2
    direction = player['direction']
    step = 0.1

    # Generate points along the direction
    points = []
    if direction == 0:  # North
        points = [(x, y - i * step) for i in range(int(distance / step) + 1)]
    elif direction == 1:  # South
        points = [(x, y + i * step) for i in range(int(distance / step) + 1)]
    elif direction == 2:  # East
        points = [(x + i * step, y) for i in range(int(distance / step) + 1)]
    elif direction == 3:  # West
        points = [(x - i * step, y) for i in range(int(distance / step) + 1)]

    # Check each point for collision with players
    for p in players:
        if p['index'] != player_id:
            for point in points:
                if point_in_object(point, p):
                    return True

    # Check each point for collision with carts
    for cart in carts:
        if cart["owner"] == player_id and isHoldingCart:
            continue  # Skip the cart being held by the player
        for point in points:
            if point_in_object(point, cart):
                return True

    return False


def obstacle_in_aisle(player_id, state, shopping_item, direction):
    """
    Determine if the aisle above or below the shelf with the specified item is blocked.

    Args:
        player_id (int): ID of the player to check around.
        state (dict): Current game state.
        shopping_item (str): The shopping item to locate which aisle.
        direction (str): 'above' or 'below' to specify which aisle to check.

    Returns:
        bool: True if the aisle is blocked, False otherwise.
    """
    shelves = [
        ["milk", "chocolate milk", "strawberry milk"],
        ["apples", "oranges", "banana", "strawberry", "raspberry"],
        ["sausage", "steak", "chicken", "ham"],
        ["brie cheese", "swiss cheese", "cheese wheel"],
        ["garlic", "leek", "red bell pepper", "carrot", "lettuce"],
        ["avocado", "broccoli", "cucumber", "yellow bell pepper", "onion"]
    ]

    aisle_y_coords = [
        (2.55, 5.1),  # Aisle 1
        (6.5, 9.05),  # Aisle 2
        (10.6, 12.9),  # Aisle 3
        (14.5, 17),  # Aisle 4
        (18.65, 21.1),  # Aisle 5
        (22.5, 24)  # Aisle 6
    ]

    # Find which shelf the item is on
    shelf_index = next(i for i, shelf in enumerate(shelves) if shopping_item in shelf)

    # Determine the aisles to check based on the shelf index and direction
    if direction == "above":
        if shelf_index == 0:
            aisle_to_check = aisle_y_coords[shelf_index]
        else:
            aisle_to_check = aisle_y_coords[shelf_index - 1]
    elif direction == "below":
        aisle_to_check = aisle_y_coords[shelf_index]

    x_start, x_end = 5.25, 15.25
    y_start, y_end = aisle_to_check

    # Rectangle for the aisle
    aisle_rect = {'position': (x_start, y_start), 'width': x_end - x_start, 'height': y_end - y_start}

    # Check for obstacles in the aisle
    players = state['observation']['players']
    carts = state['observation']['carts']
    player = players[player_id]
    isHoldingCart = player['curr_cart'] != -1

    # Check players
    for p in players:
        if p['index'] == player_id:
            continue  # Skip the player themselves
        player_point = (p['position'][0], p['position'][1])
        if point_in_object(player_point, aisle_rect):
            return True

    # Check carts
    for cart in carts:
        if cart["owner"] == player_id and isHoldingCart:
            continue  # Skip the cart held by the player
        cart_point = (cart['position'][0], cart['position'][1])
        if point_in_object(cart_point, aisle_rect):
            return True

    return False

# import json
# import socket
# from utils import recv_socket_data
# # Connect to Supermarket
# HOST = '127.0.0.1'
# PORT = 9000
# sock_game = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock_game.connect((HOST, PORT))
#
# for i in range(10):
#     # sock_game.send(str.encode("0 TOGGLE_CART"))
#     sock_game.send(str.encode("0 EAST"))
#     state = recv_socket_data(sock_game)
#     state = json.loads(state)
# print(obstacle_in_aisle(0, state, "milk", "above"))

# state_json = json.dumps(state, indent=4)
# print(state["observation"]["players"][0]["position"])
