import logging
import os
import sys
import json
from brain.brain import BrainComponent
from report.report_converter import ReportGenerator
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


class Chatastrophe:
    def __init__(self, uuid, chatbot_name, chatbot_url, attack_types):
        self.uuid = uuid
        self.chatbot_name = chatbot_name
        self.chatbot_url = chatbot_url
        self.attack_types = attack_types
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.progress = {}
        for attack_type in attack_types:
            self.progress[attack_type] = {
                "completed_attacks": 0,
                "total_attacks": 0,
                "completed": 0,
                "total": 100
            }

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG)
        # Create a log file specific to this UUID
        os.makedirs('logs', exist_ok=True)
        log_file = f'logs/{self.uuid}.log'
        
        # Remove any pre-existing handlers to prevent conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        # Define a clean log format
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        
        # Configure logging with both file and console handlers
        logging.basicConfig(
            level=logging.DEBUG,
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Silence noisy libraries
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("httpcore").setLevel(logging.ERROR)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    def get_progress(self):
        """Return the current progress state"""
        return self.progress
    
    def save_final_progress(self):
        """Save the final progress to a file"""
        os.makedirs('reports', exist_ok=True)
        progress_file = f'reports/{self.uuid}_progress.json'
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.progress, f)
            self.logger.info(f"Final progress saved to {progress_file}")
        except Exception as e:
            self.logger.error(f"Error saving progress: {str(e)}")

    def run(self):
        self.logger.info("Chatastrophe app started")
        brain = BrainComponent(chatbot_name=self.chatbot_name, chatbot_url=self.chatbot_url)
        relevant_categories = [category for category in brain.attack_categories if category.name in self.attack_types]

        # Initialize total attack counts
        for category in relevant_categories:
            category_name = category.name
            if category_name in self.progress:
                self.progress[category_name]["total_attacks"] = len(category.attacks)
                self.progress[category_name]["total"] = 100  # Percentage scale

        # Execute attacks and track progress
        for category in relevant_categories:
            category_name = category.name
            total_attacks = len(category.attacks)
            
            for i, attack in enumerate(category.attacks):
                brain.execute_attack(attack)
                
                # Update progress for this category
                if category_name in self.progress:
                    self.progress[category_name]["completed_attacks"] = i + 1
                    self.progress[category_name]["completed"] = int((i + 1) / total_attacks * 100) if total_attacks > 0 else 100

        generator = ReportGenerator(brain)
        report = generator.generate_report()
        
        # Mark all attacks as complete - ensure all attacks show as completed
        for category in relevant_categories:
            category_name = category.name
            if category_name in self.progress:
                total_attacks = self.progress[category_name]["total_attacks"]
                self.progress[category_name]["completed_attacks"] = total_attacks
                self.progress[category_name]["completed"] = 100
        
        # Save the final progress information to a file
        self.save_final_progress()

        with open(rf"./reports/{self.uuid}.html", 'w', encoding="utf-8", errors="backslashreplace") as file:
            file.write(report)
        
        self.logger.info(f"Chatastrophe app finished - f{self.uuid}")

