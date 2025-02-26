from typing import Dict, Any
import requests
import logging


class IntegrationComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

    def send_message_api(
        self, url: str, message: str, headers: Dict = None
    ) -> Dict[str, Any]:
        """Send message to chatbot using REST API"""
        try:
            payload = {"message": message}
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def send_attack_command(
        self, url: str, prompt: str, headers: Dict = None
    ) -> Dict[str, Any]:
        try:
            self.logger.info(f"Sending attack prompt: {prompt}")
            response = self.send_message_api(
                url=url, message=prompt, headers=headers
            )
            return {
                'prompt': prompt,
                'response': response,
            }
        except Exception as e:
            self.logger.error(f"Attack command failed: {str(e)}")
            raise
