from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class SecOpsState(TypedDict):
    # The conversational history and tool calls
    messages: Annotated[list[BaseMessage], add_messages]
    
    # What the agent discovers during its investigation phase
    findings: str
    
    # The specific commands the agent plans to execute
    planned_actions: List[str]
    
    # Tracks whether the security issue has been successfully resolved
    is_remediated: bool