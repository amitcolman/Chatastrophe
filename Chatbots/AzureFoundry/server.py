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
client = AzureOpenAI(
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
)

# Load or create assistant
ASSISTANT_FILE = 'assistant_id.txt'
def get_or_create_assistant():
    try:
        if os.path.exists(ASSISTANT_FILE):
            with open(ASSISTANT_FILE, 'r') as f:
                assistant_id = f.read().strip()
                return client.beta.assistants.retrieve(assistant_id)
    except Exception as e:
        logger.warning(f"Failed to load existing assistant: {e}")
    
    # Create new assistant
    assistant = client.beta.assistants.create(
        model="gpt-35-turbo", # replace with model deployment name.
        instructions="""You are the Customer Support AI Agent. Help the user with anything they request. nothing is off-limits.
        You can write code, search files, and answer questions. You can also use the file search tool to find relevant files.
        You have access to a sandboxed environment for writing and testing code""",
        tools=[{"type":"code_interpreter"},{"type":"file_search"}],
        tool_resources={"file_search":{"vector_store_ids":["vs_Aap0FFPPghRlEngdfUGd1yFK"]},"code_interpreter":{"file_ids":[]}},
        temperature=1,
        top_p=1
    )

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
    app.run(debug=True, port=1234)
