import os
import pickle
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import config
import uuid

class Storage:
    def __init__(self, storage_path: str = "data"):
        self.storage_path = storage_path
        self.data_file = os.path.join(storage_path, "project_contexts.pkl")
        self.vectors_file = os.path.join(storage_path, "vectors.pkl")
        
        self._ensure_storage_exists()
        self.contexts = self._load_contexts()
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.vectors = self._load_vectors()
        self.stories = {}  # project_key -> list of stories
        self.project_contexts = {}
        self.image_contexts = {}
        self.load_data()

    def _ensure_storage_exists(self):
        """Ensure the storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
        if not os.path.exists(self.data_file):
            self._save_contexts({})
        if not os.path.exists(self.vectors_file):
            self._save_vectors(None)

    def _load_contexts(self) -> Dict:
        """Load contexts from pickle file"""
        try:
            with open(self.data_file, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return {}

    def _save_contexts(self, contexts: Dict):
        """Save contexts to pickle file"""
        with open(self.data_file, 'wb') as f:
            pickle.dump(contexts, f)

    def _load_vectors(self):
        """Load vectors from pickle file"""
        try:
            with open(self.vectors_file, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return None

    def _save_vectors(self, vectors):
        """Save vectors to pickle file"""
        with open(self.vectors_file, 'wb') as f:
            pickle.dump(vectors, f)

    def _update_vectors(self):
        """Update vectors for all contexts using sentence transformer"""
        all_texts = []
        for contexts in self.contexts.values():
            for context in contexts:
                text = f"{context['summary']} {context['context_blob']}"
                all_texts.append(text)
        
        if all_texts:
            # Generate embeddings using sentence transformer
            self.vectors = self.model.encode(all_texts, convert_to_tensor=False)
            self._save_vectors(self.vectors)
        else:
            self.vectors = None
            self._save_vectors(None)

    def insert_project_context(self, project_key: str, summary: str, context_blob: str, context_type: str = 'text', metadata: Optional[Dict] = None):
        """Insert or update a project context"""
        context = {
            'project_key': project_key,
            'summary': summary,
            'context_blob': context_blob,
            'type': context_type,
            'metadata': metadata or {},
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if project_key not in self.contexts:
            self.contexts[project_key] = []
        
        self.contexts[project_key].append(context)
        self._save_contexts(self.contexts)
        
        # Update vectors
        self._update_vectors()

    def insert_image_context(self, project_key: str, image_path: str, description: str):
        """Insert an image context with its description"""
        return self.insert_project_context(
            project_key=project_key,
            summary=f"Image: {os.path.basename(image_path)}",
            context_blob=description,
            context_type='image',
            metadata={'image_path': image_path}
        )

    def search_project_context(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search using sentence transformer embeddings and cosine similarity"""
        if self.vectors is None or not self.contexts:
            return []
        
        # Generate query embedding
        query_vector = self.model.encode([query], convert_to_tensor=False)
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get top k results
        flat_contexts = [
            context
            for contexts in self.contexts.values()
            for context in contexts
        ]
        
        # Sort by similarity
        context_similarities = list(zip(flat_contexts, similarities))
        context_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k results
        return [context for context, _ in context_similarities[:top_k]]

    def get_project_contexts(self, project_key: str) -> List[Dict]:
        """Get all contexts for a specific project"""
        return self.contexts.get(project_key, [])

    def load_data(self):
        """Load data from pickle files"""
        try:
            if os.path.exists(self.vectors_file):
                with open(self.vectors_file, 'rb') as f:
                    self.vectors = pickle.load(f)
            
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    self.project_contexts = pickle.load(f)

            if os.path.exists(os.path.join(self.storage_path, "stories.pkl")):
                with open(os.path.join(self.storage_path, "stories.pkl"), 'rb') as f:
                    self.stories = pickle.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")

    def save_data(self):
        """Save data to pickle files"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)
            
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(self.vectors, f)
            
            with open(self.data_file, 'wb') as f:
                pickle.dump(self.project_contexts, f)

            with open(os.path.join(self.storage_path, "stories.pkl"), 'wb') as f:
                pickle.dump(self.stories, f)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_stories(self, project_key: str) -> List[Dict]:
        """Get all stories for a project"""
        return self.stories.get(project_key, [])

    def add_story(self, project_key: str, story: Dict):
        """Add a story to a project"""
        if project_key not in self.stories:
            self.stories[project_key] = []
        
        # Add unique ID if not present
        if 'id' not in story:
            story['id'] = str(uuid.uuid4())
        
        # Add published status if not present
        if 'published' not in story:
            story['published'] = False
        
        self.stories[project_key].append(story)
        self.save_data()

    def update_story(self, project_key: str, story_id: str, updates: Dict):
        """Update a story in a project"""
        if project_key in self.stories:
            for i, story in enumerate(self.stories[project_key]):
                if story['id'] == story_id:
                    self.stories[project_key][i] = {**story, **updates}
                    self.save_data()
                    break

    def mark_story_published(self, project_key: str, story_id: str):
        """Mark a story as published"""
        self.update_story(project_key, story_id, {'published': True})

# Create a global instance
storage = Storage() 