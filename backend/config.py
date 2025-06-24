from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Model configurations
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # Only OpenAI supported
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')
EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'openai')  # Only OpenAI supported
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

# Jira configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Confluence configuration
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME')
CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')

class Config:
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Model configurations
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # Only OpenAI supported
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")  # Only OpenAI supported
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # RAG settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "3"))
    
    # JIRA settings (optional)
    JIRA_URL: Optional[str] = os.getenv("JIRA_URL")
    JIRA_USERNAME: Optional[str] = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")

    # Confluence settings (optional)
    CONFLUENCE_URL: Optional[str] = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_USERNAME: Optional[str] = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN: Optional[str] = os.getenv("CONFLUENCE_API_TOKEN")

# Create a global instance
config = Config()
