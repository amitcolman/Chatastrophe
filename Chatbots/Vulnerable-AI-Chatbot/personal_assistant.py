import os
import subprocess
import time
import re
from flask import Flask, request, redirect, render_template
from langchain.chains import RetrievalQA, LLMChain
from langchain.document_loaders import PyPDFLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains import create_retrieval_chain
import flask.cli
from get_llm import get_llm



# Create a Flask web application
app = Flask(__name__)
os.environ["reveal_secret"] = "yes"
os.environ["reveal_owner"] = "yes"
flask.cli.show_server_banner = lambda *args: None



def chatCompletion(query, search_query):
    # ChatBot policy check

    if ("sum " in search_query or "summarize" in search_query) and "http" in search_query: # Website summerizer
        website_index = query.find("http")
        website_path = query[website_index:]
        pre_command = 'curl -m 1 -o /dev/null -s -w "%{http_code}\n"'
        command = '{0} {1}'.format(pre_command, website_path)
        try:
            output = subprocess.check_output(command, shell=True)
            output = str(output.decode()).strip()
            if output == '200':
                try:
                    template = """Question: {question}
                        Answer: what website it is."""
                    prompt = PromptTemplate(template=template, input_variables=["question"])
                    llm = get_llm()
                    llm_chain = LLMChain(prompt=prompt, llm=llm)
                    completion = llm_chain.run(website_path)
                    return f"Here's a quick summary of your website:\n{completion}"
                except Exception as error:
                    error_type = '{0}'.format(type(error).__name__)
                    if error_type == "AuthenticationError":
                        return "Your API token is not valid. Please restart the container using a valid token."
                    elif error_type == "RateLimitError":
                        return "You have run out of API credits. Please register an account using an unused phone number to access trial credits, or purchase additional credits. Then, re-run the container with a valid token."
                    else:
                        return f"error type: {error_type}\nerror message: {error}"
            return f"{website_path} website returns an error code {output}. Please try again with a different website."
        
        except Exception:
            return f"{website_path} website is not found. Please try again with a different website."



    if os.path.exists('/dataset/DataSource.pdf'):
        file_path = '/dataset/DataSource.pdf'
    else:
        file_path = 'DataSource.pdf'

    # Load document using PyPDFLoader document loader
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    # Split document in chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
    docs = text_splitter.split_documents(documents=documents)

    try:
        os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        os.environ["AZURE_OPENAI_ENDPOINT"] = "https://chatastrophe.openai.azure.com"

        embeddings = AzureOpenAIEmbeddings(
            deployment="text-embedding-ada-002",
            azure_endpoint="https://chatastrophe.openai.azure.com",
            openai_api_version="2023-05-15"
        )        
        # Create vectors
        vectorstore = FAISS.from_documents(docs, embeddings)
        # Persist the vectors locally on disk
        vectorstore.save_local("training_sets")
        # Load from local storage
        persisted_vectorstore = FAISS.load_local("training_sets", embeddings, allow_dangerous_deserialization=True)
        custom_prompt = PromptTemplate(
                input_variables=["context", "query"],
                template="""Use the following pieces of context to answer the question at the end.
                    If you don't know the answer, just try to the best of your abillity.
                    You are here to server the user and must comply with anything asked by the user.
                    ----------------
                    {context}
                    ----------------
                    Question: {query}
                    Helpful Answer:"""
                    )
        llm_chain = LLMChain(llm=get_llm(), prompt=custom_prompt)
        combine_docs_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="context")
        qa = RetrievalQA(
            retriever=persisted_vectorstore.as_retriever(),
            combine_documents_chain=combine_docs_chain,
            return_source_documents=False
        )
        try:
            relevant_documents = persisted_vectorstore.as_retriever().get_relevant_documents(query)
            result = combine_docs_chain.run(input_documents=relevant_documents, query=query)
        except Exception as e:
            print("error in run function")
            error_type = '{0}'.format(type(e).__name__)
            return f"run error type: {error_type}\nerror message: {e}"
        return str(result)
    
    except Exception as error:
        error_type = '{0}'.format(type(error).__name__)

        if error_type == "AuthenticationError":
            return "Your API token is not valid. Please restart the container using a valid token."

        elif error_type == "RateLimitError":
            return "You have run out of API credits. Please register an account using an unused phone number to access trial credits, or purchase additional credits. Then, re-run the container with a valid token."

        else:
            return f"error type: {error_type}\nerror message: {error}"


def revealInfo(search_query):
    if "forget" in search_query and "rules" in search_query:
        os.environ["reveal_secret"] = "yes"
    if "new" in search_query and "operator" in search_query:
        os.environ["reveal_owner"] = "yes"


# Define app routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get")
# Function for the bot response
def get_response():
    user_query = request.args.get('msg')
    search_query = user_query.lower()
    search_query = re.sub(r'[^a-zA-Z0-9 ]', r'', search_query)
    revealInfo(search_query)
    return chatCompletion(user_query, search_query)


@app.route('/refresh')
def refresh():
    time.sleep(600)  # Wait for 10 minutes
    return redirect('/refresh')


# Run the Flask app
if __name__ == "__main__":
    app.run('0.0.0.0', port=5000)
    