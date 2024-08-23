import time

#Different utilities used for returning ids and baskets


def recv_socket_data(sock):
    BUFF_SIZE = 4096  # 4 KiB
    data = b''
    while True:
        time.sleep(0.00001)
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break

    return data 

def parse_object(obj_name: str):
    return obj_name.lower().replace(' ', '_') 

def get_my_cart_id(state, playerNum):
    # my_cart_id = state['observation']['players'][playerNum] 
    # if my_cart_id != -1:
    #     return my_cart_id 
    # print(state)
    for i, cart in enumerate(state['observation']['carts']):
        if cart['owner'] == playerNum:
            return i 
        
    return -1 # You don't have a cart 

def get_my_basket_id(state, playerNum):
    # my_basket_id = state['observation']['players'][playerNum] 
    # if my_basket_id != -1:
    #     return my_basket_id 
    for i, basket in enumerate(state['observation']['baskets']):
        if basket['owner'] == playerNum:
            return i 
        
    return -1 # You don't have a basket


def get_cart_or_basket_id(state, player_id, cart_or_basket):
    assert (cart_or_basket == "carts" or cart_or_basket == "baskets"), "invalid cart_or_basket value!"
    if cart_or_basket == "carts":
        return get_my_cart_id(state, playerNum=player_id)
    elif cart_or_basket == "baskets":
        return get_my_basket_id(state, playerNum=player_id)
