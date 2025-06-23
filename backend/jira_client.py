import os
from typing import Dict, List, Optional, Tuple, Union
import requests
from config import config

class JiraClientError(Exception):
    """Exception raised for errors in Jira client"""
    pass

class JiraClient:
    def __init__(self):
        self.base_url: Optional[str] = config.JIRA_URL
        self.auth: Tuple[str, str] = (
            str(config.JIRA_USERNAME) if config.JIRA_USERNAME else "",
            str(config.JIRA_API_TOKEN) if config.JIRA_API_TOKEN else ""
        )
        self.is_configured: bool = all([self.base_url, self.auth[0], self.auth[1]])

    def create_user_story(self, project_key: str, summary: str, description: str) -> Dict:
        """Create a user story in Jira"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")

        url = f"{self.base_url}/rest/api/2/issue"
        
        # Prepare the issue data
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Story"}  # Assuming "Story" is a valid issue type in your Jira
            }
        }

        try:
            response = requests.post(
                url,
                json=issue_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Failed to create Jira issue: {str(e)}")

    def create_user_stories_from_rag(self, project_key: str, stories: List[str]) -> List[Dict]:
        """Create multiple user stories from RAG output"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")

        results = []
        for story in stories:
            # Extract summary from the first line of the story
            lines = story.strip().split('\n')
            summary = lines[0].replace('As a ', '')  # Remove "As a" prefix for cleaner summary
            
            # Use the full user story as description
            description = story
            
            try:
                result = self.create_user_story(project_key, summary, description)
                results.append(result)
            except JiraClientError as e:
                results.append({"error": str(e), "story": story})
        
        return results

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[Dict]:
        """Fetch issues from a Jira project"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")
            
        url = f"{self.base_url}/rest/api/2/search"
        
        try:
            response = requests.get(
                url,
                params={
                    "jql": f"project={project_key}",
                    "maxResults": max_results
                },
                auth=self.auth
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    "id": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "description": issue["fields"]["description"] or "",
                    "status": issue["fields"]["status"]["name"],
                    "updated": issue["fields"]["updated"]
                }
                for issue in data["issues"]
            ]
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Failed to fetch Jira issues: {str(e)}")

    def create_epic(self, project_key: str, summary: str, description: str) -> Dict:
        """Create an epic in Jira"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")

        url = f"{self.base_url}/rest/api/2/issue"
        
        # Prepare the epic data
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Epic"}
            }
        }

        try:
            response = requests.post(
                url,
                json=issue_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Failed to create Jira epic: {str(e)}")

    def link_story_to_epic(self, epic_key: str, story_key: str) -> Dict:
        """Link a story to an epic"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")

        # First, get the epic link field name
        fields_url = f"{self.base_url}/rest/api/2/field"
        try:
            fields_response = requests.get(
                fields_url,
                auth=self.auth
            )
            fields_response.raise_for_status()
            fields = fields_response.json()
            epic_link_field = next(
                (field['id'] for field in fields if field['name'] == 'Epic Link'),
                None
            )
            
            if not epic_link_field:
                raise JiraClientError("Could not find Epic Link field in Jira")

            # Update the story with the epic link
            update_url = f"{self.base_url}/rest/api/2/issue/{story_key}"
            update_data = {
                "fields": {
                    epic_link_field: epic_key
                }
            }
            
            update_response = requests.put(
                update_url,
                json=update_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )
            update_response.raise_for_status()
            
            return {"message": f"Successfully linked {story_key} to epic {epic_key}"}
            
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Failed to link story to epic: {str(e)}")

    def create_epic_with_stories(self, project_key: str, epic_summary: str, epic_description: str, stories: List[Dict[str, str]]) -> Dict:
        """Create an epic and its associated stories"""
        try:
            # Create the epic
            epic_result = self.create_epic(project_key, epic_summary, epic_description)
            epic_key = epic_result["key"]
            
            # Create stories and link them to the epic
            story_results = []
            for story in stories:
                try:
                    # Create the story
                    story_result = self.create_user_story(
                        project_key=project_key,
                        summary=story["summary"],
                        description=story["description"]
                    )
                    
                    # Link the story to the epic
                    self.link_story_to_epic(epic_key, story_result["key"])
                    story_results.append(story_result)
                except Exception as e:
                    # Log the error but continue with other stories
                    story_results.append({
                        "error": str(e),
                        "story": story
                    })
            
            return {
                "epic": epic_result,
                "stories": story_results
            }
            
        except Exception as e:
            raise JiraClientError(f"Failed to create epic with stories: {str(e)}")

    def fetch_projects(self) -> List[Dict]:
        """Fetch all accessible Jira projects"""
        if not self.is_configured:
            raise JiraClientError("Jira integration is not configured")
            
        url = f"{self.base_url}/rest/api/2/project"
        
        try:
            response = requests.get(
                url,
                auth=self.auth
            )
            response.raise_for_status()
            
            return [{
                "id": project["id"],
                "key": project["key"],
                "name": project["name"]
            } for project in response.json()]
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Failed to fetch Jira projects: {str(e)}")

# Create a global instance
jira_client = JiraClient() 