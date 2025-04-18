import os

from langchain.chat_models import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_community.chat_models import ChatOllama

from .settings import settings


# Create ChatGPT model for chat.
def create_chat_openai_model():
    os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://chatastrophe.openai.azure.com"
    llm = AzureChatOpenAI(
        azure_deployment="o3-mini",
        api_version="2024-12-01-preview",
        openai_api_type="azure",
        temperature=0,
        timeout=None
    )
    # llm = ChatOpenAI(
    #     openai_api_key=settings.OPENAI_API_KEY,
    #     model_name=settings.OPENAI_MODEL_NAME,
    #     max_tokens=settings.OPENAI_MAX_TOKENS,
    #     temperature=settings.OPENAI_TEMPERATURE,
    #     verbose=settings.OPENAI_VERBOSE,
    #     openai_api_base="https://api.openai.com/v1"
    # )
    # llm = ChatOllama(
    #     model="openhermes",  # or "openhermes", "dolphin-mistral", etc.
    #     base_url="http://ollama:11434",  # Default Ollama API URL
    #     temperature=settings.OPENAI_TEMPERATURE,
    #     max_tokens=settings.OPENAI_MAX_TOKENS,
    #     verbose=settings.OPENAI_VERBOSE
    # )
    return llm
