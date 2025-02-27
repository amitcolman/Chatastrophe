import logging
import os

import yaml
from classes import AttackCategory, Attack

class BrainComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.attack_categories: list[AttackCategory] = []

    def load_attack_categories(self):
        attack_files = os.listdir(os.path.join(os.path.dirname(__file__), "../attacks"))
        for attack_file in attack_files:
            with open(os.path.join(os.path.dirname(__file__), "../attacks", attack_file), "r") as f:
                attack_category_yaml = yaml.safe_load(f)
                attack_category = AttackCategory.from_yaml(attack_category_yaml)
                self.attack_categories.append(attack_category)


if __name__ == "__main__":
    brain = BrainComponent()
    brain.load_attack_categories()
    print(brain.attack_categories[0].attacks[0].prompt)

