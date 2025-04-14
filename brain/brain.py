import logging
import os
from typing import List, Optional

import yaml

from integration.integration import IntegrationComponent
from .classes import AttackCategory, Attack
from enums.owasp_llm import OwaspLLM
from dotenv import load_dotenv
from .ai_client import AIClient


class BrainComponent:
    def __init__(self, chatbot_name: str, chatbot_url: str):
        self.logger = logging.getLogger(__name__)

        self.chatbot_name = chatbot_name
        self.chatbot_url = chatbot_url

        self.attack_categories: list[AttackCategory] = []
        self.load_attack_categories()

        self.successful_attacks: List[Attack] = []
        self.failed_attacks: List[Attack] = []

        self.ai_client = AIClient()

        load_dotenv()

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

        integration_instance = IntegrationComponent(name=self.chatbot_name, url=self.chatbot_url)
        response = integration_instance.send_attack_command(attack.prompt)
        self.logger.debug(f"Attack response: {response}")

        is_attack_successful = self.validate_attack_response(attack, response)
        if is_attack_successful:
            attack.chatbot_output.append(response["data"])
            self.successful_attacks.append(attack)
        else:
            if response["status"] == 200 and response["data"]:
                attack.chatbot_output.append(response["data"])
            self.failed_attacks.append(attack)

        self.logger.info(f"Attack {attack.name} was successful: {is_attack_successful}")

    def validate_attack_response(self, attack: Attack, response: Optional[dict]) -> bool:
        """
        Process the response of an attack

        @param attack: The attack
        @param response: The response

        @return: True if the attack was successful, False otherwise
        """
        self.logger.info(f"Processing attack response for {attack.name}")

        if not response:
            self.logger.error("No response received for attack")
            return False

        if response["status"] != 200:
            return False

        data = response.get("data", None)
        if not data or not isinstance(data, str):
            self.logger.error("Invalid response data")
            return False

        if not attack.expected_outputs and not attack.use_ai_if_bad_output:
            self.logger.error("No expected outputs defined for attack")
            return False

        # First try simple string matching to check if the attack was successful
        # This is a basic check and may not be reliable
        if attack.expected_outputs:
            for expected_output in attack.expected_outputs:
                if expected_output.lower() in data.lower():
                    return True

        # If string matching failed and AI analysis is enabled, use AI to analyze
        if attack.use_ai_if_bad_output:
            if not attack.ai_analysis_prompt:
                self.logger.error("No AI analysis prompt defined for attack, but use_ai_if_bad_output is True")
                return False

            self.logger.info(f"Using AI to analyze response for attack: {attack.name}")
            analysis = self.ai_client.analyze_response(attack=attack, response=data)

            if analysis["success"]:
                self.logger.info(f"AI analysis determined attack succeeded: {analysis['reason']}")
                return True
            elif analysis["blocked"]:
                self.logger.info(f"AI analysis determined attack was blocked: {analysis['reason']}")
                return False
            # elif analysis["follow_up_prompt"]:
            #     self.logger.info(f"AI suggested follow-up prompt: {analysis['follow_up_prompt']}")
            #     # Store the follow-up prompt for potential future use
            #     attack.follow_up_prompt = analysis["follow_up_prompt"]

        return False

    def convert_results_to_report(self):
        pass
