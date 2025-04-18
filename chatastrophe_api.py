from flask import Flask
import yaml
from flask import request, jsonify
import uuid
from threading import Thread, enumerate
from chatastrophe import Chatastrophe
from enums.owasp_llm import OwaspLLM
import os

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


def run_chatastrophe(chatbot_name, chatbot_url, attack_types, uuid):
    chatastrophe = Chatastrophe(uuid=uuid, chatbot_name=chatbot_name, chatbot_url=chatbot_url,
                                attack_types=attack_types)
    chatastrophe.run()
    return


@app.route('/perform-attack', methods=['POST'])
def perform_attack():
    """
    Perform attack on a chatbot
    input: URL, chatbot type, attack types, API token
    output: Attack ID
    """

    data = request.json
    chatbot_url = data.get("url", "")
    chatbot_name = data.get("name", "")
    attack_types = data.get("attack_types", [])

    # Validate chatbot type
    chatbots = get_chatbots()
    if chatbot_name not in [chatbot.get("name") for chatbot in chatbots]:
        return jsonify({"error": "Unsupported chatbot"}), 400

    # Generate a unique attack ID
    attack_id = str(uuid.uuid4())

    # Start the BrainComponent in a background thread
    chatastrophe = Thread(target=run_chatastrophe, args=(chatbot_name, chatbot_url, attack_types, attack_id),
                          name=f"{attack_id}")
    chatastrophe.start()

    return jsonify({"attack_id": attack_id}), 200


@app.route('/get-report', methods=['GET'])
def get_report():
    data = request.get_json()
    attack_id = data.get("attack_id", "")

    # Check if the attack_id is running in the background
    for thread in enumerate():
        if thread.name == attack_id:
            return jsonify({"status": "Attack in progress"}), 200

    # Check if the report file exists
    report_file_path = f"./reports/{attack_id}.html"
    if os.path.exists(report_file_path):
        with open(report_file_path, 'r') as file:
            report_data = file.read()
        return jsonify({"status": "completed", "report": report_data}), 200

    return jsonify({"status": "attack not found"}), 404


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


@app.route('/get-attack-categories', methods=['GET'])
def get_attack_categories():
    """ 
    Load available attack categories from attack_categories.yaml
    input: API token
    output: List of available attack categories
    """

    attack_categories = OwaspLLM.get_all_categories()
    return jsonify(attack_categories), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3333)
