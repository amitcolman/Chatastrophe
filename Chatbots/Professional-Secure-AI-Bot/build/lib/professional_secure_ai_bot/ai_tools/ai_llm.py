import os

from langchain_openai import ChatOpenAI

# Establishes one central place for the LLM, to make it adjustable


def get_llm() -> ChatOpenAI:
    """Returns the LLM, this allows for a central place to change the LLM to other providers or local."""
    os.environ["OPENAI_API_KEY"] = os.getenv(
        "OPENAI_API_KEY"
    )  # Looks weird, but somehow necessary
    azure_endpoint = "https://chatastrophe.openai.azure.com/"
    llm = ChatOpenAI(base_url=azure_endpoint)
    return llm
