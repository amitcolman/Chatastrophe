from flask import Flask
import yaml
from flask import request, jsonify
import uuid
from threading import Thread, enumerate
from chatastrophe import Chatastrophe
from enums.owasp_llm import OwaspLLM
import os

app = Flask(__name__)

# Track active Chatastrophe instances
active_jobs = {}

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


def run_chatastrophe(chatbot_url, attack_types, uuid):
    global active_jobs
    chatastrophe = Chatastrophe(uuid=uuid, chatbot_url=chatbot_url,
                                attack_types=attack_types)
    active_jobs[uuid] = chatastrophe
    
    try:
        chatastrophe.run()
        # The save_final_progress method is already called in run()
    except Exception as e:
        app.logger.error(f"Error in chatastrophe run: {str(e)}")
    finally:
        # Cleanup when done
        if uuid in active_jobs:
            del active_jobs[uuid]
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
    attack_types = data.get("attack_types", [])


    # Generate a unique attack ID
    attack_id = str(uuid.uuid4())

    # Start the BrainComponent in a background thread
    chatastrophe = Thread(target=run_chatastrophe, args=(chatbot_url, attack_types, attack_id),
                          name=f"{attack_id}")
    chatastrophe.start()

    return jsonify({"attack_id": attack_id}), 200


@app.route('/get-report', methods=['GET'])
def get_report():
    data = request.get_json()
    attack_id = data.get("attack_id", "")
    
    # Check if the attack is active and get progress
    if attack_id in active_jobs:
        progress = active_jobs[attack_id].get_progress()
        return jsonify({
            "status": "Attack in progress",
            "progress": progress
        }), 200

    # Check for thread by name (backward compatibility)
    thread_running = False
    for thread in enumerate():
        if thread.name == attack_id:
            thread_running = True
            break
    
    if thread_running:
        return jsonify({"status": "Attack in progress"}), 200

    # Check if the report file exists
    report_file_path = f"./reports/{attack_id}.html"
    progress_file_path = f"./reports/{attack_id}_progress.json"
    
    if os.path.exists(report_file_path):
        with open(report_file_path, 'r', encoding="utf-8", errors="backslashreplace") as file:
            report_data = file.read()
        
        # Try to get final progress data if available
        final_progress = {}
        if os.path.exists(progress_file_path):
            try:
                with open(progress_file_path, 'r') as progress_file:
                    import json
                    final_progress = json.load(progress_file)
            except Exception as e:
                app.logger.error(f"Error loading progress data: {str(e)}")
        
        return jsonify({
            "status": "completed", 
            "report": report_data,
            "progress": final_progress
        }), 200

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
