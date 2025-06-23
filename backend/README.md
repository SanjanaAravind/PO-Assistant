# Verba - The Golden RAGtriever

A simple RAG (Retrieval-Augmented Generation) system for project context management.

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following content:
```env
# Server settings
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Storage settings
STORAGE_PATH=./data

# Google AI settings (for Gemini)
GOOGLE_API_KEY=your_api_key_here

# Jira settings (optional)
JIRA_URL=your_jira_url
JIRA_USERNAME=your_username
JIRA_API_TOKEN=your_api_token

# Confluence settings (optional)
CONFLUENCE_URL=your_confluence_url
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token
```

## Running the Application

1. Make sure your virtual environment is activated

2. Run the application:
```bash
python run.py
```

The API will be available at http://127.0.0.1:8000

## API Documentation

Once the application is running, you can access:
- API documentation: http://127.0.0.1:8000/docs
- Alternative API documentation: http://127.0.0.1:8000/redoc

## Features

### Core Features
- Store and retrieve project context
- Vector-based semantic search using SentenceTransformers
- Persistent storage for text and image data
- Integration with LLM providers (Gemini) for RAG
- Support for multiple data sources in a unified context

### Data Sources
1. **Jira Integration**
   - Fetch and index Jira tickets
   - Automatic context extraction from ticket fields
   - Configurable project and result limits

2. **Confluence Integration**
   - Sync Confluence pages into the knowledge base
   - HTML to text conversion for better context extraction
   - Support for space-based or search-based page fetching
   - Create new pages through API

3. **Image Processing**
   - Upload and store project-related images
   - Automatic image description using Gemini Vision
   - Include image contexts in RAG responses
   - Images stored in filesystem with metadata in vector store

4. **BRD Processing**
   - Upload and section Business Requirement Documents
   - Generate epics and user stories from BRD content
   - Semantic search across BRD sections

### Usage Examples

1. Upload an image:
```bash
curl -X POST "http://localhost:8000/upload_image" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/image.jpg" \
  -F "project_key=YOUR_PROJECT"
```

2. Ask questions about any content:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "YOUR_PROJECT",
    "question": "What does the architecture diagram show?"
  }' 