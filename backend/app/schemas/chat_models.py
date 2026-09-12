from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's prompt or question")
    project_key: str = Field(default="ADURG", description="Target Jira project key")
    jira_url: Optional[str] = Field(default=None, description="Optional Jira base URL")
    email: Optional[str] = Field(default=None, description="Optional Jira user email")
    api_token: Optional[str] = Field(default=None, description="Optional Jira API token")
    thread_id: Optional[str] = Field(default="default-thread", description="Session ID for conversation memory")


class ChatResponse(BaseModel):
    response: str
    project_key: str
    thread_id: str
    tool_calls: List[Dict[str, Any]] = []