# Project Management Assistant

A project management application that uses AI to help generate and manage project artifacts, including user stories, epics, and documentation.

## Features

- AI-powered chat interface for project-related queries
- Automatic story generation from project context
- Integration with Jira for story management
- Integration with Confluence for documentation
- BRD (Business Requirements Document) processing and analysis
- Image processing and context extraction

## Tech Stack

### Backend
- Python with FastAPI
- Google's Gemini AI for LLM capabilities
- Sentence Transformers for embeddings
- Integration with Jira and Confluence APIs

### Frontend
- React with TypeScript
- Modern UI components
- Real-time chat interface

## Setup

### Prerequisites
- Python 3.11+
- Node.js 16+
- Jira account (optional)
- Confluence account (optional)
- Google Gemini API key

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Create a .env file with your configuration:
   ```
   GEMINI_API_KEY=your_api_key
   JIRA_URL=your_jira_url
   JIRA_USERNAME=your_username
   JIRA_API_TOKEN=your_token
   CONFLUENCE_URL=your_confluence_url
   CONFLUENCE_USERNAME=your_username
   CONFLUENCE_API_TOKEN=your_token
   ```

4. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the frontend:
   ```bash
   npm start
   ```

The application will be available at http://localhost:3000

## Project Structure

- `/backend` - FastAPI backend application
  - `/data` - Storage for embeddings and images
  - `main.py` - Main application file
  - `rag_engine.py` - RAG implementation
  - `llm_providers.py` - LLM integration
  - Other utility modules

- `/frontend` - React frontend application
  - `/src` - Source code
    - `/components` - React components
    - `/services` - API services
    - `/contexts` - React contexts

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 