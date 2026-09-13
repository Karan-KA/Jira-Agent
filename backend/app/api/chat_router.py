import os
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.schemas.chat_models import ChatRequest, ChatResponse
from app.schemas.jira_models import ProjectConnectionRequest
from app.services.workspace_service import JiraClient
from app.services.mcp_tools import set_active_jira_client
from app.graph.jira_agent import build_jira_agent_graph


router = APIRouter(prefix="/api/v1/chat", tags=["Agent Chat"])

def get_agent_and_client(req: ChatRequest):
    """Initializes the Jira client and compiles the LangGraph agent."""
    jira_url = req.jira_url or os.getenv("JIRA_INSTANCE_URL")
    user_email = req.email or os.getenv("JIRA_USER_EMAIL")
    api_token = req.api_token or os.getenv("JIRA_API_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not all([jira_url, user_email, api_token, gemini_key]):
        raise HTTPException(
            status_code=400,
            detail="Missing Jira credentials or GEMINI_API_KEY in request/environment."
        )
    # Initialize Jira context
    project_key = req.project_key or os.getenv("PROJECT_KEY")
    conn = ProjectConnectionRequest(
        jira_url=jira_url,
        email=user_email,
        api_token=api_token,
        project_key=req.project_key
    )
    client = JiraClient(conn)
    set_active_jira_client(client)
    agent = build_jira_agent_graph(gemini_key)
    return agent

@router.post("", response_model=ChatResponse)
async def chat_sync(req: ChatRequest):
    """
    Standard synchronous chat endpoint.
    Waits for agent to complete all tool calls and returns final JSON.
    """
    agent = get_agent_and_client(req)
    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "active_project_key": req.project_key
    }
    result = await agent.ainvoke(initial_state)
    last_msg = result["messages"][-1]
    
    # Extract text content safely
    content = last_msg.content
    if isinstance(content, list):
        content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
    return ChatResponse(
        response=str(content),
        project_key=req.project_key,
        thread_id=req.thread_id
    )

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Streams tool-calling events and agent thought processes in real-time.
    """
    agent = get_agent_and_client(req)
    async def event_generator():
        initial_state = {
            "messages": [HumanMessage(content=req.message)],
            "active_project_key": req.project_key
        }
        # Stream step-by-step state transitions from LangGraph
        async for event in agent.astream_events(initial_state, version="v2"):
            event_type = event.get("event")
            # 1. When agent decides to call a tool
            if event_type == "on_tool_start":
                tool_name = event.get("name")
                tool_input = event.get("data", {}).get("input")
                yield f"event: tool_start\ndata: {json.dumps({'tool': tool_name, 'input': tool_input})}\n\n"
            # 2. When tool execution finishes
            elif event_type == "on_tool_end":
                tool_name = event.get("name")
                yield f"event: tool_end\ndata: {json.dumps({'tool': tool_name, 'status': 'completed'})}\n\n"
            # 3. When LLM generates token chunks
            elif event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and chunk.content:
                    text = chunk.content
                    if isinstance(text, list):
                        text = "".join([t.get("text", "") for t in text if isinstance(t, dict)])
                    yield f"event: token\ndata: {json.dumps({'token': text})}\n\n"
        # 4. Stream completion
        yield f"event: done\ndata: {json.dumps({'status': 'finished'})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

