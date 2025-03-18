import logging

import os
import sys
from brain.brain import BrainComponent

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    logger.info("Test app started")
    brain = BrainComponent()
    brain.execute_attack(brain.attack_categories[0].attacks[0])

