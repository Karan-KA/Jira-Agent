import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.graph.agent_state import AgentState
from app.services.mcp_tools import JIRA_AGENT_TOOLS

SYSTEM_PROMPT_TEMPLATE = """You are Jira Copilot, a helpful, natural, and highly intelligent QA & Software Engineering Assistant for project '{project_key}'.
Your goal is to understand human intent effortlessly, whether the user speaks casually or formally.
### 💡 Core Guidelines:
1. **Be Conversational & Natural:** Speak like an experienced Senior Developer / QA Lead. Explain things clearly and format your responses with clean markdown (bullet points, bold text).
2. **Intelligent Key Resolution:**
   - If the user says "ticket 10", "issue 10", or just "10", resolve it to "{project_key}-10".
   - If the user asks about general topics (e.g., "find login tests", "what bugs do we have?"), use your search tools with flexible queries.
3. **Smart Tool Usage:**
   - Call `get_jira_ticket_details` when asked about specific tickets.
   - Call `search_jira_tickets` when asked to find, list, or filter issues.
   - Call `get_project_overview` when asked about team lead, components, or overall status.
4. **Graceful Clarifications:** If something is ambiguous, provide the best answer you can from Jira and politely ask if they'd like more details.
"""


def build_jira_agent_graph(gemini_api_key: str):
    """
    Builds and compiles the LangGraph ReAct agent powered by Gemini and Jira tools.
    """
    # 1. Initialize Gemini with Tool Calling capabilities
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=gemini_api_key,
        temperature=0.0
    )
    
    # Bind the Jira MCP tools to the model
    llm_with_tools = llm.bind_tools(JIRA_AGENT_TOOLS)
    
    # 2. Define the Agent Node (Reasoner)
    async def agent_node(state: AgentState):
        project_key = state.get("active_project_key", "SCRUM")
        system_prompt = SystemMessage(
            content=SYSTEM_PROMPT_TEMPLATE.format(project_key=project_key)
        )
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

     # 3. Define the Tool Node (Executor)
    tool_node = ToolNode(JIRA_AGENT_TOOLS)

    # 4. Define Conditional Edge Router (Should we call tools or finish?)
    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        # If the LLM returned tool calls, route to tool execution
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, finish and return answer to user
        return END


# 5. Assemble the Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    # After tools execute, loop back to the agent so it can interpret the results
    workflow.add_edge("tools", "agent")
    # Compile the graph
    return workflow.compile()

