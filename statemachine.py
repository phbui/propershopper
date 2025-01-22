import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StateMachine:
    def __init__(self, agent):
        self.agent = agent
        self.state = "Idle"
        self.sub_state = None
        self.shopping_index = 0  # Tracks progress through the shopping list

    def handle_state(self):
        logging.info(f"Current State: {self.state}")
        match self.state:
            case "Idle":
                self.handle_idle()
            case "GetBasket":
                self.handle_get_basket()
            case "Shop":
                self.handle_shop()
            case "Leave":
                self.handle_leave()

    def handle_idle(self):
        logging.info("Handling 'Idle' state.")
        if not self.agent.has_basket():
            logging.info("Agent does not have a basket. Transitioning to 'GetBasket'.")
            self.state = "GetBasket"
        elif self.agent.get_shopping_list():
            logging.info("Agent has a shopping list. Transitioning to 'Shop'.")
            self.state = "Shop"
        else:
            logging.info("No basket and no shopping list. Transitioning to 'Leave'.")
            self.state = "Leave"

    def handle_get_basket(self):
        logging.info("Handling 'GetBasket' state.")
        if self.agent.move_to("basket return", self.agent.basket_return_position()):
            logging.info("Agent has reached the basket return position. Attempting to interact.")
            self.agent.interact()
            if self.agent.has_basket():
                logging.info("Agent successfully picked up a basket. Transitioning to 'Shop'.")
                self.state = "Shop"
            else:
                logging.warning("Agent failed to pick up a basket. Staying in 'GetBasket'.")

    def handle_shop(self):
        shopping_list = self.agent.get_shopping_list()
        logging.info(f"Handling 'Shop' state. Shopping list: {shopping_list}")

        if not shopping_list:
            logging.info("Shopping list is empty. Transitioning to 'Leave'.")
            self.state = "Leave"
            return

        current_item = shopping_list[self.shopping_index]
        logging.info(f"Current item to shop: {current_item}. Sub-state: {self.sub_state}")

        match self.sub_state:
            case None:
                logging.info("Initializing sub-state to 'MoveToItemLocation'.")
                self.sub_state = "MoveToItemLocation"
            case "MoveToItemLocation":
                item_position = self.agent.get_item_location(current_item)
                logging.info(f"Moving to item location: {item_position}")
                if self.agent.move_to(current_item, item_position):
                    logging.info("Agent reached item location. Transitioning to 'InteractWithItemLocation'.")
                    self.sub_state = "InteractWithItemLocation"
            case "InteractWithItemLocation":
                logging.info("Interacting with item location.")
                self.agent.interact()
                if self.agent.item_in_hand(current_item) or self.agent.item_in_cart(current_item) or self.agent.item_in_basket(current_item):
                    logging.info(f"Successfully picked up item: {current_item}")
                    self.shopping_index += 1
                    if self.shopping_index >= len(shopping_list):
                        logging.info("Completed shopping list. Transitioning to 'Leave'.")
                        self.state = "Leave"
                    else:
                        logging.info("Moving to the next item in the shopping list.")
                        self.sub_state = "MoveToItemLocation"
                else:
                    logging.warning("Failed to pick up the item. Returning to 'MoveToItemLocation'.")
                    self.sub_state = "MoveToItemLocation"

    def handle_leave(self):
        logging.info("Handling 'Leave' state.")
        if self.agent.leave():
            logging.info("Agent successfully reached the exit and left the store.")
            self.sub_state = "Done"
