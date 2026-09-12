import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.graph.agent_state import AgentState
from app.services.mcp_tools import JIRA_AGENT_TOOLS


def build_jira_agent_graph(gemini_api_key: str):
    """
    Builds and compiles the LangGraph ReAct agent powered by Gemini and Jira tools.
    """
    # 1. Initialize Gemini with Tool Calling capabilities
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=gemini_api_key,
        temperature=0.0
    )
    
    # Bind the Jira MCP tools to the model
    llm_with_tools = llm.bind_tools(JIRA_AGENT_TOOLS)
    
    # 2. Define the Agent Node (Reasoner)
    def agent_node(state: AgentState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
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

