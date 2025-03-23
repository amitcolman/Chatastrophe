from flask import Flask
import yaml
from flask import request, jsonify
import re
import uuid

app = Flask(__name__)

def is_valid_token(token):
    return token == "chatastrophe_token"

@app.before_request
def check_auth():
    """check authorization before every request"""

    token = request.headers.get("Authorization")
    if not is_valid_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    

def get_chatbots():
    with open('./Chatbots/chatbots.yaml', 'r') as file:
        chatbots_data = yaml.safe_load(file)
        return chatbots_data.get("chatbots", [])


@app.route('/perform-attack', methods=['POST'])
def perform_attack():
    """
    Perform attack on a chatbot
    input: URL, chatbot type, attack types, API token
    output: Attack ID
    """

    data = request.json
    chatboot_url = data.get("url", "")
    chatbot_name = data.get("name", "")
    attack_types = data.get("attack_types", [])


    # Validate chatbot type
    chatbots = get_chatbots()
    if chatbot_name not in [chatbot.get("name") for chatbot in chatbots]:
        return jsonify({"error": "Unsupported chatbot"}), 400

    # # Validate attack types
    # Todo: Implement this
    if False and (not isinstance(attack_types, list) or not all(
        attack in [] for attack in attack_types)):
        return jsonify({"error": "Invalid attack types"}), 400

    attack_id = str(uuid.uuid4())

    #Todo:
    # implement brain thread to execute attack

    return attack_id, 200 
  

@app.route('/get-report', methods=['GET'])
def get_report():
    # Functionality to be implemented
    pass

@app.route('/get-available-chatbots', methods=['GET'])
def get_available_chatbots():
    """ 
    Load available chatbots from chatbots.yaml
    input: API token
    output: List of available chatbots
    """

    available_chatbots = []
    for chatbot in get_chatbots():
        available_chatbots.append({
            "name": chatbot.get("name"),
            "type": chatbot.get("type"),
            "fields": chatbot.get("fields")
        })
    return jsonify({"available_chatbots": available_chatbots}), 200
    
if __name__ == '__main__':
    app.run(debug=True, port=80)