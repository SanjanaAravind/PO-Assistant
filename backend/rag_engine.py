from typing import Dict, Any, Optional, List
from storage import storage
from llm_providers import DummyLLMProvider, OpenAIProvider, LLMProvider
from config import config

class LLMProviderError(Exception):
    """Exception raised for errors in LLM providers"""
    pass

class RAGEngine:
    def __init__(self):
        self.providers = {
            "dummy": DummyLLMProvider(),
            "openai": OpenAIProvider()
        }
        # Set provider based on configuration
        provider_name = config.LLM_PROVIDER
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found. Available providers: {list(self.providers.keys())}")
        self.current_provider = self.providers[provider_name]

    def set_provider(self, provider_name: str):
        """Set the current LLM provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found. Available providers: {list(self.providers.keys())}")
        self.current_provider = self.providers[provider_name]

    def set_default_provider(self):
        """Set the default provider (from config)"""
        provider_name = config.LLM_PROVIDER
        if provider_name not in self.providers:
            raise ValueError(f"Default provider {provider_name} not found. Available providers: {list(self.providers.keys())}")
        self.current_provider = self.providers[provider_name]

    def run_pipeline(self, project_key: str, user_question: str) -> str:
        """Run the RAG pipeline"""
        try:
            # Search for relevant context
            context = storage.search_project_context(user_question)
            
            # Generate response using the current provider
            response = self.current_provider.generate_response(context, user_question)
            
            return response
        except Exception as e:
            raise LLMProviderError(f"Error in RAG pipeline: {str(e)}")

    def chat(self, message: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """Handle chat messages with optional context"""
        try:
            # Initialize empty context list if None
            context_list = context if context is not None else []
            
            # Generate response using the current provider
            response = self.current_provider.generate_response(context_list, message)
            return response
        except Exception as e:
            raise LLMProviderError(f"Error in chat: {str(e)}")

# Create a global instance
rag_engine = RAGEngine() 