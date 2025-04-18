import logging

import os
import sys
from brain.brain import BrainComponent
from report.report_converter import ReportGenerator

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


def setup_logging():
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


setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Test app started")
    brain = BrainComponent(chatbot_name="rag-chatbot", chatbot_url="http://localhost:5000/rag-chatbot/ask")
    # The first attack fails
    # brain.execute_attack(brain.attack_categories[0].attacks[0])
    # brain.execute_attack(brain.attack_categories[0].attacks[1])
    for category in brain.attack_categories:
        for attack in category.attacks:
            brain.execute_attack(attack)

    generator = ReportGenerator(brain)
    report = generator.generate_report()
