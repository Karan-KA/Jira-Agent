import base64
import json
from typing import Optional, List, Dict, Any
import httpx
from app.schemas.jira_models import ProjectConnectionRequest, ProjectMetadata, JiraIssue
class JiraClient:
    """
    Enterprise Universal Client for Atlassian Jira Cloud REST API v3.
    """
    def __init__(self, credentials: ProjectConnectionRequest):
        self.base_url = str(credentials.jira_url).rstrip("/")
        self.user_email = credentials.user_email if hasattr(credentials, 'user_email') else credentials.email
        self.api_token = credentials.api_token
        self.project_key = credentials.project_key.upper()
        auth_string = f"{self.user_email}:{self.api_token}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    async def test_and_connect_project(self) -> ProjectMetadata:
        """Handshake to fetch project metadata."""
        endpoint = f"{self.base_url}/rest/api/3/project/{self.project_key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return ProjectMetadata(
                    project_key=self.project_key,
                    project_name=data.get("name", self.project_key),
                    lead_name=data.get("lead", {}).get("displayName", "Unassigned"),
                    description=data.get("description", ""),
                    issue_types=[it.get("name") for it in data.get("issueTypes", [])],
                    components=[c.get("name") for c in data.get("components", [])],
                    is_connected=True
                )
            raise Exception(f"Jira API error ({response.status_code}): {response.text}")
    async def raw_jql_search(self, jql: str, max_results: int = 25) -> str:
        """Universal JQL search executor."""
        endpoint = f"{self.base_url}/rest/api/3/search/jql"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "status", "issuetype", "priority", "assignee", "description", "created", "updated"]
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("issues", []):
                    f = item.get("fields", {})
                    
                    desc = f.get("description")
                    desc_text = ""
                    if isinstance(desc, dict):
                        try:
                            desc_text = desc.get("content", [{}])[0].get("content", [{}])[0].get("text", "")
                        except Exception:
                            desc_text = str(desc)
                    elif isinstance(desc, str):
                        desc_text = desc
                    results.append({
                        "key": item.get("key"),
                        "summary": f.get("summary", ""),
                        "issue_type": f.get("issuetype", {}).get("name", ""),
                        "status": f.get("status", {}).get("name", ""),
                        "priority": f.get("priority", None),
                        "assignee": f.get("assignee", {}).get("displayName", "Unassigned") if f.get("assignee") else "Unassigned",
                        "description": desc_text[:200]
                    })
                return json.dumps(results, indent=2)
            else:
                return f"Jira JQL Error ({response.status_code}): {response.text}"
    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Universal fetch for any ticket."""
        endpoint = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                f = data.get("fields", {})
                
                desc = f.get("description")
                desc_text = ""
                if isinstance(desc, dict):
                    try:
                        desc_text = desc.get("content", [{}])[0].get("content", [{}])[0].get("text", "")
                    except Exception:
                        desc_text = str(desc)
                elif isinstance(desc, str):
                    desc_text = desc
                return {
                    "key": data.get("key"),
                    "summary": f.get("summary", ""),
                    "issue_type": f.get("issuetype", {}).get("name", ""),
                    "status": f.get("status", {}).get("name", ""),
                    "priority": f.get("priority", {}).get("name", "Medium"),
                    "assignee": f.get("assignee", {}).get("displayName", "Unassigned") if f.get("assignee") else "Unassigned",
                    "description": desc_text,
                    "created": f.get("created"),
                    "updated": f.get("updated")
                }
            raise Exception(f"Issue {issue_key} not found: {response.text}")