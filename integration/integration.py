from typing import Dict, Any, List, Optional
import requests
import logging
import json


class IntegrationComponent:
    def __init__(self, url: str):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.url = url
        self.full_url = url
        self.params: Dict[str, Any] = {}

    def _try_request(self, url: str, method: str, message: str, **kwargs) -> Dict[str, Any]:
        """Attempt a request with given parameters"""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            data = ""
            if response.text:
                try:
                    data = response.json()
                    if isinstance(data, dict) and not self.params.get('response_field'):
                        response_field = next((k for k in ['response', 'answer', 'text', 'output', 'result', 'data', 'reply'] 
                                            if k in data), None)
                        if response_field:
                            self.params['response_field'] = response_field
                except json.JSONDecodeError:
                    self.params['response_field'] = "response"
                    data = {"response": response.text}
            return {
                "status": response.status_code,
                "data": data
            }

        except requests.exceptions.HTTPError as e:
            return {
                "status": e.response.status_code,
                "data": {"error": str(e)}
            }

        except requests.RequestException as e:
            return {
                "status": None,
                "error": f"Request failed: {str(e)}"
            }


    def replace_strings(self, obj, message):
        if isinstance(obj, dict):
            return {k: self.replace_strings(v, message) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_strings(item, message) for item in obj]
        elif isinstance(obj, str):
            return message
        else:
            return obj




    def send_message_api(self, url: str, message: str) -> Dict[str, Any]:
        """Smart message sender that tries different request methods and parameter structures"""
        
        if hasattr(self, 'params') and self.params:
            # Build the body fresh for each request
            if self.params.get('method') == 'GET':
                params = {self.params['param_name']: message}
                json_data = None
                data_data = None
            elif self.params.get('method') == 'POST':
                body_template = self.params.get('body_template')
                if isinstance(body_template, dict) or isinstance(body_template, list):
                    body = self.replace_strings(body_template, message)
                else:
                    body = message
                params = None
                json_data = body if isinstance(body, (dict, list)) else None
                data_data = body if isinstance(body, str) else None
            else:
                params = None
                json_data = None
                data_data = None
            response = self._try_request(
                self.params['url'],
                self.params['method'],
                message,
                params=params,
                json=json_data,
                data=data_data,
                headers=self.params.get('headers', {})
            )
            if response and response["status"] in [200, 201]:
                return response['data'].get(self.params.get('response_field'))

        # Common parameter names used in APIs
        param_names = ['message', 'text', 'query', 'q', 'prompt', 'input', 'msg']
        
        # List of endpoints to try (empty string first, then common endpoints)
        endpoints = ['/llm4shell-lv1', '/chat', '/get', '/api', '/query', '/ask', '']
        for endpoint in endpoints:
            full_url = f"{url.rstrip('/')}{endpoint}"
            error404 = False

            for param in param_names:
                self.logger.info(f"attempting to requests {full_url} with: {param}")

                # Try GET with different parameter names
                response = self._try_request(
                    full_url, 
                    'GET',
                    message,
                    params={param: message}
                )
                if response and response["status"] in [200, 201] and not response['data']['response'].strip().startswith('<!DOCTYPE html>'):
                    headers = {'Content-Type': 'application/json'}
                    self.params = {
                        'method': 'GET',
                        'url': full_url,
                        'param_name': param,
                        'headers': headers,
                        **self.params
                    }
                    self.full_url = full_url
                    return response['data'].get(self.params.get('response_field'))

                elif response and response["status"] == 404: # Not Found
                    error404 = True
                    break

                elif response and response["status"] == 405: # Method Not Allowed
                    break

            if error404:
                continue

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
                headers = {'Content-Type': 'application/json'} if isinstance(body, (dict, list)) else {'Content-Type': 'text/plain'}
                response = self._try_request(
                    full_url,
                    'POST',
                    message,
                    json=body if isinstance(body, (dict, list)) else None,
                    data=body if isinstance(body, str) else None,
                    headers=headers
                )
                if response and response["status"] in [200, 201]:
                    # Store only the structure, not the actual message
                    body_template = body if isinstance(body, (dict, list)) else None
                    self.params = {
                        'method': 'POST',
                        'url': full_url,
                        'body_template': body_template,
                        'headers': headers,
                        **self.params
                    }
                    self.full_url = full_url
                    return response['data'].get(self.params.get('response_field'))

        # If all attempts fail, return error
        return {
            "status": 400,
            "data": "Failed to find a working request method and structure"
        }

    def send_attack_command(self, prompt: str) -> Dict[str, Any]:
        """Send an attack command using the smart message sender"""
        try:
            return {"status": 200, "data": self.send_message_api(url=self.url, message=prompt), "endpoint": self.full_url}
        except Exception as e:
            return {"status": 400, "data": {"error": str(e)}, "endpoint": self.full_url}