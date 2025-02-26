from typing import Dict, Any
import requests
import logging


class IntegrationComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

    def send_message_api(self, url: str, message: str, headers: Dict = None, max_retries: int = 3) -> Dict[str, Any]:
        """Send message to chatbot using REST API with retries"""
        if headers is None:
            headers = {}
        headers['Connection'] = 'keep-alive'
        headers['Protocol'] = 'HTTP/1.1'
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json={"question": message}, headers=headers)
                #print (response.headers)
                response.raise_for_status()
                return {"status": 200, "response": response.json().get("answer")}
            except Exception as e:
                self.logger.warning(f"API connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries: 
                    #self.logger.error("Max retries reached for API connection")
                    return {"status": 503, "data": "Unable to connect to the chatbot after multiple attempts"}
            
    def send_attack_command(self, url: str, prompt: str, headers: Dict = None) -> Dict[str, Any]:
        try:
            response = self.send_message_api(url=url, message=prompt, headers=headers)
            return {"status": response["status"], "data": response["response"]}
        except Exception as e:
            #self.logger.error(f"Attack command failed: {str(e)}")
            return {"status": 400, "data": {"error": str(e)}}



if __name__ == "__main__":
    integration = IntegrationComponent()
    print (integration.send_attack_command("http://localhost:5000/rag-chatbot/ask", "Hello, how are you?"))

