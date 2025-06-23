import os
from typing import Dict, List, Optional, Tuple
import requests
from config import config

class ConfluenceClientError(Exception):
    """Exception raised for errors in Confluence client"""
    pass

class ConfluenceClient:
    def __init__(self):
        # Get base Jira URL without /rest/api/2 if it's there
        jira_base = config.JIRA_URL.split('/rest/api')[0] if config.JIRA_URL else None
        # Construct Confluence URL - Confluence Cloud API uses /wiki/rest/api
        self.base_url: Optional[str] = f"{jira_base}/wiki" if jira_base else None
        self.auth: Tuple[str, str] = (
            str(config.JIRA_USERNAME) if config.JIRA_USERNAME else "",
            str(config.JIRA_API_TOKEN) if config.JIRA_API_TOKEN else ""
        )
        self.is_configured: bool = all([config.JIRA_URL, self.auth[0], self.auth[1]])

    def fetch_pages(self, space_key: str, max_results: int = 50) -> List[Dict]:
        """Fetch pages from a Confluence space"""
        if not self.is_configured:
            raise ConfluenceClientError("Confluence integration is not configured")
            
        url = f"{self.base_url}/rest/api/content"
        
        try:
            response = requests.get(
                url,
                params={
                    "spaceKey": space_key,
                    "type": "page",
                    "expand": "body.storage,version",
                    "status": "current",
                    "maxResults": max_results
                },
                auth=self.auth
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    "id": page["id"],
                    "title": page["title"],
                    "content": page["body"]["storage"]["value"],  # This is in HTML format
                    "version": page["version"]["number"],
                    "last_modified": page["version"]["when"]
                }
                for page in data["results"]
            ]
        except requests.exceptions.RequestException as e:
            raise ConfluenceClientError(f"Failed to fetch Confluence pages: {str(e)}")

    def fetch_page_by_id(self, page_id: str) -> Dict:
        """Fetch a specific page by its ID"""
        if not self.is_configured:
            raise ConfluenceClientError("Confluence integration is not configured")
            
        url = f"{self.base_url}/rest/api/content/{page_id}"
        
        try:
            response = requests.get(
                url,
                params={
                    "expand": "body.storage,version"
                },
                auth=self.auth
            )
            response.raise_for_status()
            
            page = response.json()
            return {
                "id": page["id"],
                "title": page["title"],
                "content": page["body"]["storage"]["value"],  # This is in HTML format
                "version": page["version"]["number"],
                "last_modified": page["version"]["when"]
            }
        except requests.exceptions.RequestException as e:
            raise ConfluenceClientError(f"Failed to fetch Confluence page: {str(e)}")

    def search_pages(self, query: str, space_key: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Search for pages in Confluence"""
        if not self.is_configured:
            raise ConfluenceClientError("Confluence integration is not configured")
            
        url = f"{self.base_url}/rest/api/content/search"
        
        cql = f'type=page AND text ~ "{query}"'
        if space_key:
            cql += f' AND space="{space_key}"'
            
        try:
            response = requests.get(
                url,
                params={
                    "cql": cql,
                    "expand": "body.storage,version",
                    "maxResults": max_results
                },
                auth=self.auth
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    "id": page["id"],
                    "title": page["title"],
                    "content": page["body"]["storage"]["value"],  # This is in HTML format
                    "version": page["version"]["number"],
                    "last_modified": page["version"]["when"]
                }
                for page in data["results"]
            ]
        except requests.exceptions.RequestException as e:
            raise ConfluenceClientError(f"Failed to search Confluence pages: {str(e)}")

    def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> Dict:
        """Create a new page in Confluence"""
        if not self.is_configured:
            raise ConfluenceClientError("Confluence integration is not configured")
            
        url = f"{self.base_url}/rest/api/content"
        
        # Prepare the page data
        page_data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        # Add parent if specified
        if parent_id:
            page_data["ancestors"] = [{"id": parent_id}]

        try:
            response = requests.post(
                url,
                json=page_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConfluenceClientError(f"Failed to create Confluence page: {str(e)}")

# Create a global instance
confluence_client = ConfluenceClient() 