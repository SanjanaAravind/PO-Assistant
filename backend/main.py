from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import io
import json
from storage import storage
from rag_engine import rag_engine, LLMProviderError
from jira_client import jira_client, JiraClientError
from confluence_client import confluence_client, ConfluenceClientError
from config import config
import html2text
import tempfile
import os
import shutil
from image_processor import image_processor
from pathlib import Path

app = FastAPI(title="Verba - The Golden RAGtriever")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure images directory exists
IMAGES_DIR = Path("data/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Mount the images directory to serve static files
app.mount("/data/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

class ProjectContext(BaseModel):
    project_key: str
    summary: str
    context_blob: str

class Question(BaseModel):
    project_key: str
    question: str
    provider: Optional[str] = None

class JiraSync(BaseModel):
    project_key: str
    max_results: int = 50  # Default to 50 results

class CreateStories(BaseModel):
    project_key: str
    stories: List[str]

class GenerateStoriesRequest(BaseModel):
    project_key: str
    prompt: str
    provider: Optional[str] = None
    num_epics: Optional[int] = 1  # Number of epics to generate

class BRDUploadResponse(BaseModel):
    message: str
    project_key: str
    sections: List[Dict[str, str]]

class ConfluenceSync(BaseModel):
    space_key: str
    search_query: Optional[str] = None
    max_results: int = 50  # Default to 50 results

class CreateConfluencePage(BaseModel):
    space_key: str
    title: str
    content: str
    parent_id: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    project_key: Optional[str] = None

class StoryCreate(BaseModel):
    project_key: str
    story: Dict[str, Any]

class StoryUpdate(BaseModel):
    project_key: str
    story_id: str
    updates: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "message": "Verba API is running",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Check if all services are healthy"""
    status = {
        "status": "healthy",
        "services": {
            "storage": "connected",
            "jira": "not_configured" if not jira_client.is_configured else "connected",
            "llm_providers": []
        }
    }
    
    # Check available LLM providers
    if rag_engine.providers:
        status["services"]["llm_providers"] = list(rag_engine.providers.keys())
    else:
        status["status"] = "degraded"
        
    return status

@app.post("/store_project")
async def store(context: ProjectContext):
    """Store project context"""
    try:
        storage.insert_project_context(
            project_key=context.project_key,
            summary=context.summary,
            context_blob=context.context_blob
        )
        return {"message": "Context stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(question: Question):
    """Ask a question about the project"""
    try:
        # Set provider if specified
        if question.provider:
            try:
                rag_engine.set_provider(question.provider)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        response = rag_engine.run_pipeline(
            project_key=question.project_key,
            user_question=question.question
        )
        return {
            "answer": response,
            "provider": rag_engine.current_provider.__class__.__name__
        }
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_stories")
async def create_stories(request: CreateStories):
    """Create user stories in Jira from a list of stories"""
    if not jira_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Jira integration is not configured. Set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file."
        )

    try:
        results = jira_client.create_user_stories_from_rag(
            project_key=request.project_key,
            stories=request.stories
        )
        return {
            "message": f"Successfully created {len(results)} stories",
            "results": results
        }
    except JiraClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_jira")
async def sync_jira_data(sync: JiraSync):
    """Sync Jira issues to storage"""
    if not jira_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Jira integration is not configured. Set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file."
        )

    try:
        # Fetch issues from Jira
        issues = jira_client.fetch_issues(
            project_key=sync.project_key,
            max_results=sync.max_results
        )
        
        # Store each issue as context
        for issue in issues:
            storage.insert_project_context(
                project_key=sync.project_key,
                summary=f"Jira Issue: {issue['id']} - {issue['summary']}",
                context_blob=f"""
Issue Key: {issue['id']}
Summary: {issue['summary']}
Status: {issue['status']}
Last Updated: {issue['updated']}

Description:
{issue['description']}
""",
                context_type='jira_issue',
                metadata={
                    'issue_key': issue['id'],
                    'status': issue['status'],
                    'updated': issue['updated']
                }
            )
        
        return {
            "message": f"Successfully synced {len(issues)} issues",
            "project_key": sync.project_key
        }
    except JiraClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_and_publish_stories")
async def generate_and_publish_stories(request: GenerateStoriesRequest):
    """Generate epics with user stories using LLM and publish them to Jira"""
    if not jira_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Jira integration is not configured. Set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file."
        )

    try:
        # Set provider if specified
        if request.provider:
            try:
                rag_engine.set_provider(request.provider)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Construct a prompt that asks for epics and their stories
        epic_prompt = f"""Based on the following project context, generate {request.num_epics} epic(s) with associated user stories.
        For each epic, provide:
        1. Epic Title: A clear, concise title
        2. Epic Description: A detailed description of the epic's goals and scope
        3. User Stories: 3-5 user stories that belong to this epic

        Format each epic as follows:
        ---EPIC---
        Title: [Epic Title]
        Description: [Epic Description]
        User Stories:
        1. As a [user type], I want [goal], so that [benefit]
        Description: [Detailed description of the user story]
        2. As a [user type]...
        [and so on]
        ---END EPIC---

        Project Context:
        {request.prompt}
        """

        # Generate epics and stories using RAG engine
        generated_text = rag_engine.run_pipeline(
            project_key=request.project_key,
            user_question=epic_prompt
        )

        # Parse the generated text into epics and stories
        epics_text = generated_text.split("---EPIC---")[1:]  # Split and remove first empty part
        results = []
        
        for epic_text in epics_text:
            if not epic_text.strip():
                continue
                
            # Parse epic text
            epic_parts = epic_text.split("---END EPIC---")[0].strip().split("User Stories:")
            epic_header = epic_parts[0].strip()
            stories_text = epic_parts[1].strip() if len(epic_parts) > 1 else ""
            
            # Extract epic title and description
            epic_lines = epic_header.split("\n")
            epic_title = epic_lines[0].replace("Title:", "").strip()
            epic_description = "\n".join(line for line in epic_lines[1:] if "Description:" in line)
            epic_description = epic_description.replace("Description:", "").strip()
            
            # Parse stories
            stories = []
            current_story = {"summary": "", "description": ""}
            
            for line in stories_text.split("\n"):
                line = line.strip()
                if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                    # If we have a previous story, add it to the list
                    if current_story["summary"]:
                        stories.append(current_story.copy())
                    # Start a new story
                    current_story = {
                        "summary": line[2:].strip(),  # Remove the number and dot
                        "description": ""
                    }
                elif line.startswith("Description:"):
                    current_story["description"] = line.replace("Description:", "").strip()
            
            # Add the last story
            if current_story["summary"]:
                stories.append(current_story)
            
            # Create the epic and its stories in Jira
            jira_result = jira_client.create_epic_with_stories(
                project_key=request.project_key,
                epic_summary=epic_title,
                epic_description=epic_description,
                stories=stories
            )
            
            results.append({
                "epic": {
                    "title": epic_title,
                    "description": epic_description,
                    "jira_key": jira_result["epic"]["key"]
                },
                "stories": [
                    {
                        "summary": story["summary"],
                        "description": story["description"],
                        "jira_key": jira_story["key"]
                    }
                    for story, jira_story in zip(stories, jira_result["stories"])
                ]
            })

        return {
            "message": f"Successfully generated and created {len(results)} epics with their stories",
            "results": results,
            "provider": rag_engine.current_provider.__class__.__name__
        }
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except JiraClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_brd")
async def upload_brd(
    file: UploadFile = File(...),
    project_key: str = Form(...),
    section_size: Optional[int] = Form(default=1000)  # Characters per section
) -> BRDUploadResponse:
    """
    Upload and process a BRD file for RAG.
    The file will be split into sections and stored in the vector database.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )
    
    try:
        # Read the entire file content
        content = await file.read()
        
        # Check file size (limit to 10MB)
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB"
            )
        
        # Try different encodings
        text = None
        encodings = ['utf-8', 'ascii', 'iso-8859-1', 'cp1252', 'latin1']
        decode_errors = []
        
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                print(f"Successfully decoded file using {encoding} encoding")  # Debug log
                break
            except UnicodeDecodeError as e:
                decode_errors.append(f"{encoding}: {str(e)}")
                continue
        
        if text is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not decode file. Tried encodings: {', '.join(decode_errors)}"
            )
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split the text into sections
        sections = []
        current_section = ""
        current_title = "Main Section"  # Default title
        
        # Split text into lines and clean them
        lines = [line.strip() for line in text.split('\n')]
        
        for line in lines:
            # Skip empty lines at the start of sections
            if not line and not current_section:
                continue
            
            # Simple section detection for now to debug
            if line and not line.startswith(('-', '•', ' ')):
                # If we have content in current section, save it
                if current_section.strip():
                    sections.append({
                        "title": current_title,
                        "content": current_section.strip()
                    })
                current_section = ""
                current_title = line.strip()
            else:
                current_section += line + "\n"
        
        # Add the last section
        if current_section.strip():
            sections.append({
                "title": current_title,
                "content": current_section.strip()
            })
        
        # Ensure we have at least one section
        if not sections:
            sections.append({
                "title": "Main Section",
                "content": text.strip()
            })
        
        print(f"Created {len(sections)} sections")  # Debug log
        
        # Store sections in RAG storage
        for section in sections:
            storage.insert_project_context(
                project_key=project_key,
                summary=section["title"],
                context_blob=section["content"]
            )
        
        return BRDUploadResponse(
            message=f"Successfully processed BRD into {len(sections)} sections",
            project_key=project_key,
            sections=sections
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process BRD file: {str(e)}"
        )

class GenerateFromBRDRequest(BaseModel):
    project_key: str
    num_epics: Optional[int] = 1
    provider: Optional[str] = None
    specific_section: Optional[str] = None  # To focus on a particular section

@app.post("/generate_from_brd")
async def generate_from_brd(request: GenerateFromBRDRequest):
    """Generate epics and stories from an uploaded BRD"""
    try:
        # Get the stored BRD sections
        contexts = storage.get_project_contexts(request.project_key)
        if not contexts:
            raise HTTPException(
                status_code=404,
                detail=f"No BRD found for project key: {request.project_key}"
            )
        
        # Filter by specific section if requested
        if request.specific_section:
            contexts = [
                ctx for ctx in contexts 
                if request.specific_section.lower() in ctx['summary'].lower()
            ]
            if not contexts:
                raise HTTPException(
                    status_code=404,
                    detail=f"Section '{request.specific_section}' not found in BRD"
                )
        
        # Construct the context for story generation
        brd_context = "\n\n".join([
            f"Section: {ctx['summary']}\n{ctx['context_blob']}"
            for ctx in contexts
        ])
        
        # Use the existing generate_and_publish_stories endpoint
        stories_request = GenerateStoriesRequest(
            project_key=request.project_key,
            prompt=f"""Based on this BRD, generate appropriate epics and user stories:

{brd_context}""",
            provider=request.provider,
            num_epics=request.num_epics
        )
        
        return await generate_and_publish_stories(stories_request)
        
    except (JiraClientError, LLMProviderError) as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_confluence")
async def sync_confluence_data(sync: ConfluenceSync):
    """Fetch Confluence pages and store in storage"""
    if not confluence_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Confluence integration is not configured. Set CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN in .env file."
        )

    try:
        # Initialize HTML to text converter
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_tables = False
        h.body_width = 0  # No wrapping

        # Fetch pages based on search query or space
        if sync.search_query and isinstance(sync.search_query, str):  # Ensure search_query is a string
            pages = confluence_client.search_pages(
                query=sync.search_query,
                space_key=sync.space_key,
                max_results=sync.max_results  # Match method signature
            )
        else:
            pages = confluence_client.fetch_pages(
                space_key=sync.space_key,
                max_results=sync.max_results  # Match method signature
            )
        
        # Store each page
        for page in pages:
            # Convert HTML content to markdown/text
            content = page.get("content", "") or ""
            text_content = h.handle(content) if content else ""  # Only call handle if content is not empty
            
            storage.insert_project_context(
                project_key=sync.space_key,  # Using space_key as project_key
                summary=page["title"],
                context_blob=f"""
Page ID: {page['id']}
Title: {page['title']}
Version: {page['version']}
Last Modified: {page['last_modified']}

Content:
{text_content}
""",
                context_type='confluence_page',
                metadata={
                    'page_id': page['id'],
                    'version': page['version'],
                    'last_modified': page['last_modified']
                }
            )
        
        return {
            "message": f"Successfully synced {len(pages)} pages",
            "space_key": sync.space_key
        }
    except ConfluenceClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_confluence_page")
async def create_confluence_page(page: CreateConfluencePage):
    """Create a new page in Confluence"""
    if not confluence_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Confluence integration is not configured. Set CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN in .env file."
        )

    try:
        result = confluence_client.create_page(
            space_key=page.space_key,
            title=page.title,
            content=page.content,
            parent_id=page.parent_id
        )
        return {
            "message": "Successfully created page",
            "result": result
        }
    except ConfluenceClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/{image_name}")
async def get_image(image_name: str):
    """Serve images directly"""
    image_path = IMAGES_DIR / image_name
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path))

@app.post("/upload_image")
async def upload_image(
    file: UploadFile = File(...),
    project_key: str = Form(...)
):
    """Upload an image and process it with Gemini"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Create a temporary file with a guaranteed string path
        suffix = Path(file.filename).suffix if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        try:
            # Process the image
            result = image_processor.save_image(temp_path, project_key)
            
            # Store in RAG system
            storage.insert_image_context(
                project_key=result['project_key'],
                image_path=result['image_path'],
                description=result['description']
            )
            
            # Get the relative path for the frontend
            image_filename = os.path.basename(result['image_path'])
            image_url = f"http://localhost:8000/images/{image_filename}"
            
            return {
                "message": "Successfully processed image",
                "description": result['description'],
                "image_path": image_url,
                "filename": image_filename
            }
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
    finally:
        file.file.close()

@app.get("/jira/projects")
async def get_jira_projects():
    """Fetch all accessible Jira projects"""
    if not jira_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Jira integration is not configured. Set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file."
        )

    try:
        projects = jira_client.fetch_projects()
        return projects
    except JiraClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat endpoint that maintains minimal context"""
    try:
        # Set default provider if not already set
        if not rag_engine.current_provider:
            rag_engine.set_default_provider()
            
        # Get project context if project_key is provided
        context: List[Dict[str, Any]] = []
        if message.project_key:
            # Search for relevant context using the message as query
            context = storage.search_project_context(message.message)
        
        # Generate response using minimal context
        response = rag_engine.chat(
            message=message.message,
            context=context
        )
        
        return {
            "response": response,
            "provider": rag_engine.current_provider.__class__.__name__
        }
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stories/{project_key}")
async def get_stories(project_key: str):
    """Get all generated stories for a project"""
    try:
        # Get stories from storage
        stories = storage.get_stories(project_key)
        
        return {
            "stories": stories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stories")
async def store_story(story_data: StoryCreate):
    """Store a new story"""
    try:
        storage.add_story(story_data.project_key, story_data.story)
        return {"message": "Story stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jira/test-connection")
async def test_jira_connection():
    """Test Jira connection and return status"""
    try:
        if not jira_client.is_configured:
            return {
                "status": "not_configured",
                "message": "Jira integration is not configured. Set JIRA_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file."
            }
        
        # Try to fetch projects to test connection
        projects = jira_client.fetch_projects()
        
        return {
            "status": "connected",
            "message": "Successfully connected to Jira",
            "url": jira_client.base_url  # Return Jira URL for display
        }
    except JiraClientError as e:
        return {
            "status": "error",
            "message": f"Failed to connect to Jira: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

@app.post("/stories/{project_key}/{story_id}/publish")
async def publish_story(project_key: str, story_id: str):
    """Publish a story to Jira"""
    try:
        # Get the story from storage
        stories = storage.get_stories(project_key)
        story = next((s for s in stories if s['id'] == story_id), None)
        
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if story.get('published'):
            return {"message": "Story already published"}
        
        # Create the story in Jira
        result = jira_client.create_user_story(
            project_key=project_key,
            summary=story['title'],
            description=story['description']
        )
        
        # Mark the story as published in storage
        storage.mark_story_published(project_key, story_id)
        
        return {
            "message": "Story published successfully",
            "jira_key": result["key"]
        }
    except JiraClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/stories/{project_key}/{story_id}")
async def update_story(project_key: str, story_id: str, updates: StoryUpdate):
    """Update a story"""
    try:
        storage.update_story(project_key, story_id, updates.updates)
        return {"message": "Story updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc)
        }
    ) 