from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings


def get_embedding_function():
    embeddings = OllamaEmbeddings(model="llama3.2")
    return embeddings
