import os
from time import sleep
from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

# W
WEBHOOK_ID = os.getenv("BOTPRESS_WEBHOOK_ID")
CHAT_API_BASE = f'https://chat.botpress.cloud/{WEBHOOK_ID}'

@app.route('/')
def index():
    return send_from_directory('.', 'botpress-web.html')

@app.route('/chat', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Step 1: Create a new user
    user_payload = {
        "name": "Anonymous",
        "profile": "",
        "pictureUrl": ""
    }
    user_response = requests.post(f'{CHAT_API_BASE}/users', json=user_payload)
    if user_response.status_code not in (200, 201):
        print(f"Error code {user_response.status_code}: {user_response.content}")
        return jsonify({'error': 'Failed to create user'}), 500
    user_key = user_response.json().get('key')

    headers = {'x-user-key': user_key}

    # Step 2: Create a new conversation
    conv_response = requests.post(f'{CHAT_API_BASE}/conversations', headers=headers, json={})
    if conv_response.status_code not in (200, 201):
        print(f"Error code {conv_response.status_code}: {conv_response.content}")
        return jsonify({'error': 'Failed to create conversation'}), 500
    conversation_id = conv_response.json().get('conversation', {}).get('id')

    # Step 3: Send the user's message
    message_payload = {
        "conversationId": conversation_id,
        "payload": {
            "type": "text",
            "text": user_message
        }
    }

    message_send = requests.post(
        f'{CHAT_API_BASE}/messages',
        headers=headers,
        json=message_payload
    )
    print(headers)
    if message_send.status_code not in (200,201):
        print(f"Error code {message_send.status_code}: {message_send.content}")
        return jsonify({'error': 'Failed to send message'}), 500
    # Step 4: Retrieve the bot's response
    msg_id = message_send.json().get('message', {}).get('id')
    if not msg_id:
        return jsonify({'error': 'Failed to identify message'}), 500

    retry_counter = 0
    msg_counter = 0
    while retry_counter < 10 and msg_counter < 2:
        messages_response = requests.get(
            f'{CHAT_API_BASE}/conversations/{conversation_id}/messages/{msg_id}',
            headers=headers
        )
        if messages_response.status_code == 200:
            break
        messages_response = requests.get(
            f'{CHAT_API_BASE}/conversations/{conversation_id}/messages',
            headers=headers
        )
        if messages_response.status_code != 200:
            print(f"Error code {messages_response.status_code}: {messages_response.content}")
            return jsonify({'error': 'Failed to retrieve messages'}), 500
        try:
            messages = messages_response.json().get('messages', [])
            if not isinstance(messages, list) or not messages:
                return jsonify({'error': 'No messages found or invalid response format'}), 500
        except ValueError:
            return jsonify({'error': 'Failed to parse messages response'}), 500
        msg_counter = len(messages)
        if msg_counter < 2:
            retry_counter += 1
            print(f"Retrying... {retry_counter}")
            sleep(1)
        else:
            break

    # Return message from the bot
    bot_reply = messages[0].get('payload', {}).get('text', 'No response')

    return jsonify({'reply': bot_reply})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)