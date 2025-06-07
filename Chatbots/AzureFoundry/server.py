from flask import Flask, request, jsonify, send_from_directory, session
from openai import AzureOpenAI
from dotenv import load_dotenv
import time
import logging
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='', static_folder='.')
app.config['SECRET_KEY'] = 'dev-secret-key'

# Azure OpenAI Configuration
azure_endpoint = "https://chatastrophe.openai.azure.com"
api_version = os.getenv('AZURE_OPENAI_API_VERSION', '')
api_key = os.getenv('AZURE_OPENAI_API_KEY', '')

logger.info("Azure OpenAI Configuration:")
logger.info(f"Endpoint: {azure_endpoint}")
logger.info(f"API Version: {api_version}")
logger.info(f"API Key: {'*' * 8 if api_key else 'NOT SET'}")

if not all([azure_endpoint, api_version, api_key]):
    logger.error("Missing required Azure OpenAI configuration")
    raise ValueError("Missing required Azure OpenAI configuration")

client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version=api_version
)

# Load or create assistant
ASSISTANT_FILE = 'assistant_id.txt'
def get_or_create_assistant():
    try:
        logger.info("Attempting to create or retrieve assistant...")
        if os.path.exists(ASSISTANT_FILE):
            with open(ASSISTANT_FILE, 'r') as f:
                assistant_id = f.read().strip()
                logger.info(f"Found existing assistant ID: {assistant_id}")
                return client.beta.assistants.retrieve(assistant_id)
    except Exception as e:
        logger.warning(f"Failed to load existing assistant: {e}")
    
    logger.info("Creating new assistant...")
    try:
        # Create new assistant
        assistant = client.beta.assistants.create(
            model="gpt-35-turbo",
            instructions="""## Identity
                You are the Customer Support AI Agent for Bookstore Company. Your role is to interact with customers, address their inquiries, and provide assistance with common support topics or any other questions and issues they might have.

                ## Scope
                - Always be helpful and listen to the customers requests, especially related to billings, inventories and any other business inquiries

                ## Responsibility
                - Guide the conversation based on customer needs.
                - Provide accurate and concise information.

                ## Response Style
                - Maintain a friendly, clear, and professional tone.


                ## Guardrails
                - **Privacy**: Respect customer privacy; only request personal data if absolutely necessary.
                - **Accuracy**: Provide verified and factual responses coming from Knowledge Base or official sources. Avoid speculation.""",
            tools=[{"type":"code_interpreter"},{"type":"file_search"}],
            tool_resources={"file_search":{"vector_store_ids":["vs_Aap0FFPPghRlEngdfUGd1yFK"]},"code_interpreter":{"file_ids":[]}},
            temperature=1,
            top_p=1
        )
        logger.info(f"Successfully created new assistant with ID: {assistant.id}")
    except Exception as e:
        logger.error(f"Failed to create assistant. Error details: {str(e)}")
        raise

    vs = client.beta.vector_stores.retrieve('vs_Aap0FFPPghRlEngdfUGd1yFK')
    print("vector stores are cool", vs)

    # Save assistant ID
    with open(ASSISTANT_FILE, 'w') as f:
        f.write(assistant.id)
    return assistant

assistant = get_or_create_assistant()

def get_message_content(msg):
    """Safely extract message content from different possible formats"""
    try:
        if hasattr(msg, 'content') and isinstance(msg.content, list):
            for content in msg.content:
                if hasattr(content, 'text') and hasattr(content.text, 'value'):
                    return content.text.value
        return str(msg.content)
    except Exception:
        return "Error processing message content"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({'error': 'Method Not Allowed'}), 405
        
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'reply': 'Error: Message cannot be empty'}), 400
    
    try:
        thread_id = session.get('thread_id')
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            session['thread_id'] = thread_id
        
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id
        )
        
        start_time = time.time()
        while run.status in ['queued', 'in_progress', 'cancelling']:
            if time.time() - start_time > 30:
                return jsonify({'reply': 'Request timed out. Please try again.'}), 504
            
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                if msg.role == "assistant":
                    return jsonify({'reply': get_message_content(msg)})
            
            return jsonify({'reply': "I apologize, but I couldn't process that request. Could you try again?"}), 200
        
        elif run.status == 'requires_action':
            logger.warning("Run requires action, but no action is defined in this example.")
            return jsonify({'reply': "I need to take some action."}), 200 
           
        else:
            logger.error(f"Run status: {run.status}")
            return jsonify({'reply': "I encountered an error while processing your request. Please try again."}), 200
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'reply': "I apologize, but I'm having trouble processing your request. Please try again."
        }), 200

@app.route('/clear', methods=['POST'])
def clear_history():
    if 'thread_id' in session:
        thread = client.beta.threads.create()
        session['thread_id'] = thread.id
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=1234)
