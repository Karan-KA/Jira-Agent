from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
class AgentState(TypedDict):
    """
    The state of the conversation tracked across LangGraph execution steps.
    'add_messages' ensures new messages append to the list rather than overwriting.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    active_project_key: str