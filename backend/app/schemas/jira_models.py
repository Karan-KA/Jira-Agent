from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field

class ProjectConnectionRequest(BaseModel):
    # The four required details to connect to a specific jira project
    jira_url: HttpUrl = Field(..., description="The Jira instance URL")
    email: str = Field(..., description="The email address of the Jira user")
    api_token: str = Field(..., description="The API token for authentication")
    project_key: str = Field(..., description="The project key")


class ProjectMetadata(BaseModel):
    """Details returned upon successful project handshake."""
    project_key: str
    project_name: str
    lead_name: Optional[str] = None
    description: Optional[str] = ""
    issue_types: List[str] = []
    components: List[str] = []
    total_issues_found: int = 0
    is_connected: bool = True


class JiraIssue(BaseModel):
    """Structured model for any issue, bug, or test case."""
    key: str
    summary: str
    description: Optional[str] = ""
    status: str
    issue_type: str  # e.g., 'Test Case', 'Bug', 'Story', 'Test Plan'
    priority: str = "Medium"
    assignee: Optional[str] = "Unassigned"
    components: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    custom_fields: Dict[str, Any] = {}