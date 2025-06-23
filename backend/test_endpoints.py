import requests
import json
import os
from pathlib import Path
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None, files=None, expected_status=200):
    """Helper function to test an endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
            
        status = response.status_code
        print(f"Status: {status} (Expected: {expected_status})")
        
        if status != expected_status:
            print(f"Error: {response.text}")
        else:
            print("Response:", response.json())
            
        return status == expected_status, response.json() if status == expected_status else None
    except Exception as e:
        print(f"Error: {str(e)}")
        return False, None

def get_valid_project_key():
    """Get the first available project key from Jira"""
    success, response = test_endpoint("/jira/projects")
    if success and response:
        projects = response
        if projects:
            # Get the first project's key
            return projects[0]['key']
    return None

def run_tests():
    """Run all endpoint tests"""
    results = []
    
    # First, get a valid project key
    project_key = get_valid_project_key()
    if not project_key:
        print("\nError: No valid Jira project key found. Please ensure Jira is configured and at least one project exists.")
        sys.exit(1)
    
    print(f"\nUsing Jira project key: {project_key}")
    
    # Test root endpoint
    results.append(("Root", test_endpoint("/")[0]))
    
    # Test health check
    results.append(("Health Check", test_endpoint("/health")[0]))
    
    # Test project context storage
    project_context = {
        "project_key": project_key,
        "summary": "Test Project",
        "context_blob": "This is a test project context."
    }
    results.append(("Store Project", test_endpoint("/store_project", "POST", project_context)[0]))
    
    # Test question asking
    question = {
        "project_key": project_key,
        "question": "What is this project about?"
    }
    results.append(("Ask Question", test_endpoint("/ask", "POST", question)[0]))
    
    # Test Jira sync
    jira_sync = {
        "project_key": project_key,
        "max_results": 10
    }
    results.append(("Sync Jira", test_endpoint("/sync_jira", "POST", jira_sync)[0]))
    
    # Test BRD upload
    test_brd = "Test BRD content\nSection 1\nThis is section 1\nSection 2\nThis is section 2"
    with open("test_brd.txt", "w") as f:
        f.write(test_brd)
    
    with open("test_brd.txt", "rb") as f:
        files = {
            'file': ('test_brd.txt', f, 'text/plain'),
        }
        data = {
            'project_key': project_key,
            'section_size': '1000'
        }
        results.append(("Upload BRD", test_endpoint("/upload_brd", "POST", data=data, files=files)[0]))
    
    # Clean up test file
    os.remove("test_brd.txt")
    
    # Test generate from BRD
    generate_request = {
        "project_key": project_key,
        "num_epics": 1
    }
    results.append(("Generate from BRD", test_endpoint("/generate_from_brd", "POST", generate_request)[0]))
    
    # Test Confluence sync
    confluence_sync = {
        "space_key": project_key,  # Using project key as space key for testing
        "max_results": 10
    }
    results.append(("Sync Confluence", test_endpoint("/sync_confluence", "POST", confluence_sync)[0]))  # Changed to expect success
    
    # Test chat
    chat_message = {
        "message": "Hello",
        "project_key": project_key
    }
    results.append(("Chat", test_endpoint("/chat", "POST", chat_message)[0]))
    
    # Test get stories
    results.append(("Get Stories", test_endpoint(f"/stories/{project_key}")[0]))
    
    # Test create story
    story = {
        "project_key": project_key,
        "story": {
            "title": "Test Story",
            "description": "This is a test story"
        }
    }
    results.append(("Create Story", test_endpoint("/stories", "POST", story)[0]))
    
    # Test Jira connection
    results.append(("Test Jira Connection", test_endpoint("/jira/test-connection")[0]))
    
    # Print summary
    print("\n=== Test Summary ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print("\nDetailed Results:")
    for test, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {test}")

if __name__ == "__main__":
    run_tests() 