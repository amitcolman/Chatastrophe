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
        self.headers = self.get_chatbot_fields(name, "headers")
        self.endpoint = self.get_chatbot_fields(name, "endpoint")
        self.method = self.get_chatbot_fields(name, "method")
        self.param_name = self.get_chatbot_fields(name, "param_name")
        self.body = self.get_chatbot_fields(name, "body")
    
    def get_chatbot_fields(self, name: str, field: str) -> str:
        """
        Get chatbot fields from config file
        """
        with open("./Chatbots/chatbots.yaml", "r") as f:
            chatbots_yaml = yaml.safe_load(f)
            for chatbot in chatbots_yaml['chatbots']:
                if chatbot.get('name') == name:
                    return chatbot.get(field)

    
    def send_message_api(self, url: str, message: str, max_retries: int = 3) -> Dict[str, Any]:
        """Send a message to chatbot using REST API with retries"""

        for attempt in range(max_retries):
            try:
                url = f"{url}{self.endpoint}"
            
                if self.method.upper() == 'GET':
                    # Use param_name if specified, otherwise fall back to body.request
                    param_key = self.param_name if self.param_name else self.body['request']
                    request_params = {param_key: message}
                    response = self.session.get(url, params=request_params, headers=self.headers)
                else:  # Default to POST
                    request_params = {self.body['request']: message}
                    response = self.session.post(url, json=request_params, headers=self.headers)
            
                response.raise_for_status()
            
                # Handle string responses by converting them to JSON format
                try:
                    response_data = response.json()
                except requests.exceptions.JSONDecodeError:
                    # If the response is a string, wrap it in a JSON structure
                    response_data = {"response": response.text}
                
                return {"status": 200, "data": response_data.get(self.body['response'])}
            except Exception as e:
                self.logger.warning(f"API connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries-1:
                    return {"status": 503, "data": "Unable to connect to the chatbot after multiple attempts"}
            return None
        return None

    def send_attack_command(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.send_message_api(url=self.url, message=prompt)
            return {"status": response["status"], "data": response["data"]}
        except Exception as e:
            return {"status": 400, "data": {"error": str(e)}}