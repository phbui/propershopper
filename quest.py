
class Quest:
    def __init__(self, name):
        self.name = name
        self.requirements = []
        print(f"Created [Quest: {self.name}].")

    def __init__(self, name, requirements):
        self.name = name
        self.requirements = requirements
        print(f"Created [Quest: {self.name}].")

    def set_requirements(self, requirements):
        self.requirements = requirements

    def add_requirements(self, key, quantity):
        if key in self.requirements:
            print(f"[Quest: {self.name}] Requirement '{key}' already exists with quantity {self.requirements[key]}.")
        else:
            self.requirements[key] = quantity
            print(f"[Quest: {self.name}] Added requirement '{key}' with quantity {quantity}.")
            
    def modify_requirements(self, key, quantity):
        if key in self.requirements:
            self.requirements[key] = quantity
            print(f"[Quest: {self.name}] Modified requirement '{key}' to new quantity {quantity}.")
        else:
            print(f"[Quest: {self.name}] Requirement '{key}' does not exist.")

    def remove_requirements(self, key):
        if key in self.requirements:
            del self.requirements[key]
            print(f"[Quest: {self.name}] Removed requirement '{key}'.")
        else:
            print(f"[Quest: {self.name}] Requirement '{key}' does not exist.")
