from typing import Dict, Any, Optional, List
import google.generativeai as genai
from openai import OpenAI
from config import config

class LLMProviderError(Exception):
    """Exception raised for errors in LLM providers"""
    pass

class LLMProvider:
    """Base class for LLM providers"""
    def generate_response(self, context: List[Dict[str, Any]], question: str) -> str:
        """Generate a response using the LLM provider"""
        return "Base LLM provider does not implement response generation"

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider"""
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        if not config.LLM_MODEL:
            raise ValueError("LLM_MODEL not set in environment variables")
        
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL

    def generate_response(self, context: List[Dict[str, Any]], question: str) -> str:
        try:
            # For general chat without context
            if not context:
                # Check if the question is asking for story generation
                if any(keyword in question.lower() for keyword in ["user story", "user stories", "story", "stories"]):
                    system_prompt = """You are a helpful AI assistant. You help users with their projects and questions.
                    The user is asking about user stories. Generate appropriate user stories in the following format:

                    Story Title: [A clear, concise title for the story]
                    Description: As a [user type], I want [goal], so that [benefit]"""
                else:
                    system_prompt = """You are a helpful AI assistant. You help users with their projects and questions.
                    You can assist with project management, documentation, and general inquiries."""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]

                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    raise LLMProviderError(f"Error with OpenAI API call: {str(e)}")

            # For questions with context (RAG)
            # Check if we have any highly relevant context (similarity > 0.7)
            high_relevance_contexts = [ctx for ctx in context if ctx.get('similarity_score', 0) > 0.7]
            
            # Check if we have any moderately relevant context (0.5 <= similarity <= 0.7)
            moderate_relevance_contexts = [ctx for ctx in context if 0.5 <= ctx.get('similarity_score', 0) <= 0.7]
            
            # Format context text with relevance indicators
            context_text = ""
            if high_relevance_contexts:
                context_text += "Highly Relevant Information:\n" + "\n\n".join([
                    f"Document {i+1} (Relevance: {ctx['similarity_score']:.2f}):\nTitle: {ctx['summary']}\nContent: {ctx['context_blob']}"
                    for i, ctx in enumerate(high_relevance_contexts)
                ])
            
            if moderate_relevance_contexts:
                if context_text:
                    context_text += "\n\n"
                context_text += "Moderately Relevant Information:\n" + "\n\n".join([
                    f"Document {i+1} (Relevance: {ctx['similarity_score']:.2f}):\nTitle: {ctx['summary']}\nContent: {ctx['context_blob']}"
                    for i, ctx in enumerate(moderate_relevance_contexts)
                ])

            # If no relevant context found, acknowledge it in the response
            if not high_relevance_contexts and not moderate_relevance_contexts:
                system_prompt = """You are a helpful AI assistant. You help users with their projects and questions.
                I couldn't find any highly relevant information in the context to answer your specific question.
                I'll try my best to help based on general knowledge, but please feel free to rephrase your question
                or provide more specific details if my answer isn't sufficient."""
            else:
                # Check if the question is asking for story generation
                if any(keyword in question.lower() for keyword in ["user story", "user stories", "story", "stories"]):
                    system_prompt = """You are a helpful AI assistant. You help users with their projects and questions.
                    Based on the provided context, generate appropriate user stories in the following format:

                    Story Title: [A clear, concise title for the story]
                    Description: As a [user type], I want [goal], so that [benefit]"""
                else:
                    system_prompt = """You are a helpful AI assistant. You help users with their projects and questions.
                    Please answer based on the provided context when relevant. If the context doesn't fully answer the question,
                    you can combine it with your general knowledge to provide a complete response."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ]

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                raise LLMProviderError(f"Error with OpenAI API call: {str(e)}")

        except Exception as e:
            error_msg = f"Error generating response from OpenAI: {str(e)}"
            raise LLMProviderError(error_msg)

class GeminiProvider(LLMProvider):
    """Gemini LLM provider"""
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        if not config.LLM_MODEL:
            raise ValueError("LLM_MODEL not set in environment variables")
        
        # Configure the Gemini API
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.LLM_MODEL)

    def generate_response(self, context: List[Dict[str, Any]], question: str) -> str:
        try:
            # For general chat without context
            if not context:
                # Check if the question is asking for story generation
                if any(keyword in question.lower() for keyword in ["user story", "user stories", "story", "stories"]):
                    prompt = f"""You are a helpful AI assistant. You help users with their projects and questions.
                    The user is asking about user stories. Generate appropriate user stories in the following format:

                    Story Title: [A clear, concise title for the story]
                    Description: As a [user type], I want [goal], so that [benefit]

                    User: {question}

                    Assistant: Let me help you create some user stories. Here they are:

                    """
                else:
                    prompt = f"""You are a helpful AI assistant. You help users with their projects and questions.
                    You can assist with project management, documentation, and general inquiries.
                    
                    User: {question}
                    
                    Assistant: """
                try:
                    response = self.model.generate_content(prompt)
                    if response is None or response.text is None:
                        return "Sorry, I couldn't generate a response at this time."
                    return str(response.text)
                except Exception as e:
                    raise LLMProviderError(f"Error with Gemini API call: {str(e)}")

            # For questions with context (RAG)
            # Check if we have any highly relevant context (similarity > 0.7)
            high_relevance_contexts = [ctx for ctx in context if ctx.get('similarity_score', 0) > 0.7]
            
            # Check if we have any moderately relevant context (0.5 <= similarity <= 0.7)
            moderate_relevance_contexts = [ctx for ctx in context if 0.5 <= ctx.get('similarity_score', 0) <= 0.7]
            
            # Format context text with relevance indicators
            context_text = ""
            if high_relevance_contexts:
                context_text += "Highly Relevant Information:\n" + "\n\n".join([
                    f"Document {i+1} (Relevance: {ctx['similarity_score']:.2f}):\nTitle: {ctx['summary']}\nContent: {ctx['context_blob']}"
                    for i, ctx in enumerate(high_relevance_contexts)
                ])
            
            if moderate_relevance_contexts:
                if context_text:
                    context_text += "\n\n"
                context_text += "Moderately Relevant Information:\n" + "\n\n".join([
                    f"Document {i+1} (Relevance: {ctx['similarity_score']:.2f}):\nTitle: {ctx['summary']}\nContent: {ctx['context_blob']}"
                    for i, ctx in enumerate(moderate_relevance_contexts)
                ])

            # If no relevant context found, acknowledge it in the response
            if not high_relevance_contexts and not moderate_relevance_contexts:
                prompt = f"""You are a helpful AI assistant. You help users with their projects and questions.
                I couldn't find any highly relevant information in the context to answer your specific question.
                I'll try my best to help based on general knowledge, but please feel free to rephrase your question
                or provide more specific details if my answer isn't sufficient.

                User: {question}

                Assistant: """
            else:
                # Check if the question is asking for story generation
                if any(keyword in question.lower() for keyword in ["user story", "user stories", "story", "stories"]):
                    prompt = f"""You are a helpful AI assistant. You help users with their projects and questions.
                    Based on the provided context, generate appropriate user stories in the following format:

                    Story Title: [A clear, concise title for the story]
                    Description: As a [user type], I want [goal], so that [benefit]

                    Context:
                    {context_text}

                    User: {question}

                    Assistant: Let me help you create some user stories based on the context. Here they are:

                    """
                else:
                    prompt = f"""You are a helpful AI assistant. You help users with their projects and questions.
                    Please answer based on the provided context when relevant. If the context doesn't fully answer the question,
                    you can combine it with your general knowledge to provide a complete response.

                    Context:
                    {context_text}

                    User: {question}

                    Assistant: """

            try:
                response = self.model.generate_content(prompt)
                if response is None or response.text is None:
                    return "Sorry, I couldn't generate a response at this time."
                return str(response.text)
            except Exception as e:
                raise LLMProviderError(f"Error with Gemini API call: {str(e)}")
                
        except Exception as e:
            error_msg = f"Error generating response from Gemini: {str(e)}"
            raise LLMProviderError(error_msg)

class DummyLLMProvider(LLMProvider):
    """A dummy LLM provider that just returns a simple response"""
    def generate_response(self, context: List[Dict[str, Any]], question: str) -> str:
        if not context:
            if any(keyword in question.lower() for keyword in ["user story", "user stories", "story", "stories"]):
                return """Here are some example stories:

Story Title: Basic User Authentication
Description: As a user, I want to log in to the system, so that I can access my personalized content

Story Title: Password Reset
Description: As a registered user, I want to reset my password, so that I can regain access if I forget it"""
            return f"Hello! How can I help you with: {question}"
        context_summary = "\n".join(
            f"- {ctx['summary']}" 
            for ctx in context
        )
        return f"Question: {question}\n\nFound relevant context:\n{context_summary}" 