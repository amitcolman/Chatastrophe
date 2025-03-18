import logging
import os
from typing import List

import yaml

from integration.integration import IntegrationComponent
from .classes import AttackCategory, Attack
from enums.owasp_llm import OwaspLLM


class BrainComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.attack_categories: list[AttackCategory] = []
        self.load_attack_categories()

    def load_attack_categories(self):
        """
        Load all attack categories from the attacks directory
        """
        attack_files = os.listdir(os.path.join(os.path.dirname(__file__), "../attacks"))
        for attack_file in attack_files:
            with open(os.path.join(os.path.dirname(__file__), "../attacks", attack_file), "r") as f:
                attack_category_yaml = yaml.safe_load(f)
                attack_category = AttackCategory.from_yaml(attack_category_yaml)
                self.attack_categories.append(attack_category)

    def get_attacks_by_category(self, category_name: str) -> List[Attack]:
        """
        Get all attacks by category name

        @param category_name: The name of the category
        @return: A list of attacks
        """
        owasp_category = OwaspLLM.get_category_by_name(category_name)
        if not owasp_category:
            self.logger.error(f"Invalid OWASP category: {category_name}")
            return []

        for attack_category in self.attack_categories:
            if attack_category.category == owasp_category:
                return attack_category.attacks
        return []

    def execute_attack(self, attack: Attack):
        """
        Execute an attack

        @param attack: The attack to execute
        """
        self.logger.info(f"Executing attack: {attack.name}")

        integration_instance = IntegrationComponent()
        # TODO: Use the integration_instance to send the attack command to the chatbot
        response = "placeholder"
        self.logger.debug(f"Attack response: {response}")
        is_attack_successful = self.validate_attack_response(attack, response)


    def validate_attack_response(self, attack: Attack, response: str) -> bool:
        """
        Process the response of an attack

        @param attack: The attack
        @param response: The response

        @return: True if the attack was successful, False otherwise
        """
        self.logger.info(f"Processing attack response for {attack.name}")

        if not attack.expected_outputs:
            self.logger.error("No expected outputs defined for attack")
            return False

        for expected_output in attack.expected_outputs:
            if expected_output.lower() in response.lower():
                self.logger.info("Attack successful")
                return True

        self.logger.info("Attack unsuccessful")
        return False