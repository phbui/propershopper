import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StateMachine:
    def __init__(self, agent):
        self.agent = agent
        self.state = "Idle"
        self.sub_state = None
        self.shopping_index = 0  # Tracks progress through the shopping list

    def handle_state(self):
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
        if not self.agent.has_basket():
            self.state = "GetBasket"
        elif self.agent.shopping_list():
            self.state = "Shop"
        else:
            self.state = "Leave"

    def handle_get_basket(self):
        if self.agent.move_to("basket return", self.agent.basket_return_position()):
            self.agent.interact()
            if self.agent.has_basket():
                self.state = "Shop"

    def handle_shop(self):
        shopping_list = self.agent.shopping_list()

        if not shopping_list:
            self.state = "Leave"
            return

        current_item = shopping_list[self.shopping_index]

        match self.sub_state:
            case None:
                self.sub_state = "MoveToItemLocation"
            case "MoveToItemLocation":
                item_position = self.agent.get_item_location(current_item)
                if self.agent.move_to(current_item, item_position):
                    self.sub_state = "InteractWithItemLocation"
            case "InteractWithItemLocation":
                self.agent.interact()
                if not self.agent.item_in_hand(current_item):
                    self.sub_state = "MoveToItemLocation"
                else:
                    self.shopping_index += 1
                    if self.shopping_index >= len(shopping_list):
                        self.state = "Leave"
                    else:
                        self.sub_state = "MoveToItemLocation"


    def handle_leave(self):
        if self.agent.move_to("exit", self.agent.get_exit_position()):
            logging.info("Agent has successfully left the store.")
