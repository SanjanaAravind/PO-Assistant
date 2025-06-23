from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Gemini LLM configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # RAG settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")  # Sentence transformer model to use
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
