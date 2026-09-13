import json
from typing import List, Optional
from langchain_core.tools import tool
from app.schemas.jira_models import ProjectConnectionRequest
from app.services.workspace_service import JiraClient

active_jira_client: Optional[JiraClient] = None
def set_active_jira_client(client: JiraClient):
    global _active_jira_client
    _active_jira_client = client
def get_active_jira_client() -> JiraClient:
    if _active_jira_client is None:
        raise ValueError("No active Jira project connected. Please initialize workspace first.")
    return _active_jira_client
@tool
async def execute_jira_jql(jql_query: str) -> str:
    """
    UNIVERSAL SEARCH TOOL: Executes ANY Jira Query Language (JQL) search against the active project.
    Use this to search, filter, or list tickets, epics, bugs, or test cases.
    Examples of valid JQL:
      - All project tickets: project = 'SCRUM' ORDER BY created DESC
      - By status: project = 'SCRUM' AND status = 'In Progress'
      - By keyword in summary/desc: project = 'SCRUM' AND (summary ~ 'login' OR description ~ 'login')
      - By issue type: project = 'SCRUM' AND issuetype = 'Epic'
      - By priority: project = 'SCRUM' AND priority = 'High'
    """
    client = get_active_jira_client()
    return await client.raw_jql_search(jql_query)
@tool
async def get_jira_item(issue_key: str) -> str:
    """
    UNIVERSAL INSPECT TOOL: Retrieves full details, status, description, priority, and metadata for a specific Jira ticket, epic, or task key (e.g. SCRUM-10, SCRUM-11).
    """
    client = get_active_jira_client()
    issue = await client.get_issue(issue_key)
    return json.dumps(issue, indent=2)

# List of tools to export
JIRA_AGENT_TOOLS = [
    execute_jira_jql,
    get_jira_item
]
