from typing import Dict, Any, List, Optional
import requests
import logging
import json


class IntegrationComponent:
    def __init__(self, url: str):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.url = url
        self.params: Dict[str, Any] = {}

    def _try_request(self, url: str, method: str, message: str, **kwargs) -> Dict[str, Any]:
        """Attempt a request with given parameters"""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            try:
                data = response.json() if response.text else {}
                if isinstance(data, dict) and not self.params.get('response_field'):
                    response_field = next((k for k in ['response', 'answer', 'text', 'output', 'result', 'data'] 
                                        if k in data), None)
                    if response_field:
                        self.params['response_field'] = response_field

                return {
                    "status": response.status_code,
                    "data": data if isinstance(data, (dict, list)) else {"response": response.text}
                }
            except json.JSONDecodeError:
                return {
                    "status": response.status_code,
                    "data": {"response": response.text}
                }
        except requests.RequestException:
            return None

    def send_message_api(self, url: str, message: str) -> Dict[str, Any]:
        """Smart message sender that tries different request methods and parameter structures"""
        
        if hasattr(self, 'params') and self.params:
            response = self._try_request(
                self.params['url'],
                self.params['method'],
                message,
                params={self.params['param_name']: message} if self.params.get('method') == 'GET' else None,
                json=self.params.get('body') if self.params.get('method') == 'POST' else None,
                headers=self.params.get('headers', {})
            )
            if response and response["status"] in [200, 201]:
                return response['data'].get(self.params.get('response_field'))

        # Common parameter names used in APIs
        param_names = ['message', 'text', 'query', 'q', 'prompt', 'input', 'msg']
        
        # List of endpoints to try (empty string first, then common endpoints)
        endpoints = ['', '/llm4shell-lv1', '/api', '/chat', '/query', '/ask', '/get']
        
        for endpoint in endpoints:
            full_url = f"{url.rstrip('/')}{endpoint}"
            
            # Try GET with different parameter names
            for param in param_names:
                response = self._try_request(
                    full_url, 
                    'GET',
                    message,
                    params={param: message}
                )
                if response and response["status"] in [200, 201]:
                    headers = {'Content-Type': 'application/json'}
                    self.params = {
                        'method': 'GET',
                        'url': full_url,
                        'param_name': param,
                        'headers': headers,
                        **self.params
                    }
                    return response['data'].get(self.params.get('response_field'))

            # Try POST with different body structures
            common_body_structures = [
                {param: message} for param in param_names
            ] + [
                {"request": message},
                {"input": {"text": message}},
                {"messages": [{"content": message}]},
                message  # Try plain text body
            ]

            for body in common_body_structures:
                headers = {'Content-Type': 'application/json'} if isinstance(body, dict) else {'Content-Type': 'text/plain'}
                response = self._try_request(
                    full_url,
                    'POST',
                    message,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    headers=headers
                )
                if response and response["status"] in [200, 201]:
                    self.params = {
                        'method': 'POST',
                        'url': full_url,
                        'body': body,
                        'headers': headers,
                        **self.params
                    }
                    return response['data'].get(self.params.get('response_field'))

        # If all attempts fail, return error
        return {
            "status": 400,
            "data": "Failed to find a working request method and structure"
        }

    def send_attack_command(self, prompt: str) -> Dict[str, Any]:
        """Send an attack command using the smart message sender"""
        try:
            return {"status": 200, "data": self.send_message_api(url=self.url, message=prompt)}
        except Exception as e:
            return {"status": 400, "data": {"error": str(e)}}