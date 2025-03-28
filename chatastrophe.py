import logging

import os
import sys
from brain.brain import BrainComponent
from report.report_converter import ReportGenerator
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


class Chatastrophe:
    def __init__(self, uuid, chatbot_name, chatbot_url, attack_types):
        self.uuid = uuid
        self.chatbot_name = chatbot_name
        self.chatbot_url = chatbot_url
        self.attack_types = attack_types
        self.setup_logging()
        self.logger = logging.getLogger(__name__)


    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG)
        # Remove any pre-existing handlers to prevent conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        # Define a clean log format
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        # Configure logging properly
        logging.basicConfig(
            level=logging.DEBUG,
            format=LOG_FORMAT,
            handlers=[logging.StreamHandler(sys.stdout)],  # Ensure logs go to stdout
        )
        # Silence noisy libraries
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)



    def run(self):
        self.logger.info("Chatastrophe app started")
        brain = BrainComponent(chatbot_name=self.chatbot_name, chatbot_url=self.chatbot_url)
        relevant_categories = [category for category in brain.attack_categories if category.category.name in self.attack_types]

        for category in relevant_categories:
            for attack in category.attacks:
                brain.execute_attack(attack)

        generator = ReportGenerator(brain)
        report = generator.generate_report()
        

        with open(rf"./reports/{self.uuid}.html", 'w') as file:
            file.write(report)
        
        self.logger.info(f"Chatastrophe app finished - f{self.uuid}")

