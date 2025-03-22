from typing import Dict, Any
import requests
import logging
import yaml
import os


class IntegrationComponent:
    def __init__(self, name: str, url: str):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.name = name
        self.url = url
        self.headers = self.load_chatbot_headers(name)

    def load_chatbot_headers(self, name):
        """
        Load chatbot headers from config file
        """
        with open("./Chatbots/chatbots.yaml", "r") as f:
            chatbots_yaml = yaml.safe_load(f)
            for chatbot in chatbots_yaml['chatbots']:
                if chatbot.get('name') == name:
                    return chatbot.get('headers')

    def send_message_api(self, url: str, message: str, max_retries: int = 3) -> Dict[str, Any]:
        """Send message to chatbot using REST API with retries"""

        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json={"question": message}, headers=self.headers)
                response.raise_for_status()
                return {"status": 200, "response": response.json().get("answer")}
            except Exception as e:
                self.logger.warning(f"API connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries:
                    return {"status": 503, "data": "Unable to connect to the chatbot after multiple attempts"}

    def send_attack_command(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.send_message_api(url=self.url, message=prompt)
            return {"status": response["status"], "data": response["response"]}
        except Exception as e:
            return {"status": 400, "data": {"error": str(e)}}
