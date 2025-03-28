import os
from langchain_openai import AzureChatOpenAI

# Establishes one central place for the LLM, to make it adjustable


def get_llm() -> AzureChatOpenAI:
    os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://chatastrophe.openai.azure.com"
    llm = AzureChatOpenAI(
        azure_deployment="gpt-35-turbo",
        api_version="2025-01-01-preview",
        openai_api_type="azure",
        temperature=0,
        timeout=None
    )
    return llm