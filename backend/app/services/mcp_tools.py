import json
from typing import List, Optional
from langchain_core.tools import tool
from app.schemas.jira_models import ProjectConnectionRequest
from app.services.workspace_service import JiraClient

# Global client reference configured per active workspace session
_active_jira_client: Optional[JiraClient] = None


def set_active_jira_client(client: JiraClient):
    global _active_jira_client
    _active_jira_client = client


def get_active_jira_client() -> JiraClient:
    if _active_jira_client is None:
        raise ValueError("No active Jira project connected. Please initialize workspace first.")
    return _active_jira_client



@tool
async def get_project_overview(project_key: str) -> str:
    """
    Useful to get high-level metadata, lead, and issue types about a specific Jira project.
    """
    client = get_active_jira_client()
    metadata = await client.test_and_connect_project()
    return json.dumps({
        "project_key": metadata.project_key,
        "project_name": metadata.project_name,
        "lead": metadata.lead_name,
        "issue_types": metadata.issue_types,
        "components": metadata.components
    }, indent=2)


@tool
async def get_jira_ticket_details(issue_key: str) -> str:
    """
    Useful to retrieve detailed information, status, description, priority, and assignee for a specific Jira ticket (e.g. ADURG-1).
    """
    client = get_active_jira_client()
    issue = await client.get_issue(issue_key)
    return json.dumps(issue.model_dump(), indent=2)


@tool
async def search_jira_tickets(jql_query: str) -> str:
    """
    Useful to search Jira tickets using JQL or filter by status, assignee, priority, or issue type.
    Example query: status = 'In Progress' OR issuetype = 'Bug'
    """
    client = get_active_jira_client()
    issues = await client.search_issues_jql(jql_query)
    return json.dumps([i.model_dump() for i in issues], indent=2)


# List of tools to export
JIRA_AGENT_TOOLS = [
    get_project_overview,
    get_jira_ticket_details,
    search_jira_tickets
]


