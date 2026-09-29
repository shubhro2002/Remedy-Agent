from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from agent.llm import llm
from agent.state import SecOpsState

class RemediationPlan(BaseModel):
    findings: str = Field(description="Summary of the security vulnerabilities found.")
    planned_actions: List[str] = Field(description="List of exact AWS CLI commands to fix the issues.")

# Investigator Node
def investigator_node(state: SecOpsState):
    print("[Investigator] Analyzing the environment...")
    
    # Ensure the system prompt is present
    messages = state.get("messages", [])
    if not any(isinstance(m, SystemMessage) for m in messages):
        sys_msg = SystemMessage(content=(
            "You are an elite Cloud Security Investigator. "
            "Your job is to explore the AWS environment, find misconfigured S3 buckets "
            "(like public-read ACLs), and report them. Use your tools to investigate."
        ))
        messages = [sys_msg] + messages

    # TODO: Bind the MCP tool to this LLM in the next phase!
    response = llm.invoke(messages)
    
    return {"messages": [response]}

def drafter_node(state: SecOpsState):
    print("[Drafter] Drafting remediation plan...")
    
    # Bind the LLM to our Pydantic schema to force a structured JSON-like response
    structured_llm = llm.with_structured_output(RemediationPlan)
    
    prompt = SystemMessage(content=(
        "You are a SecOps Remediation Drafter. Review the conversation history. "
        "Draft the exact AWS CLI commands to remediate the vulnerability found by the investigator. "
        "Do NOT use destructive commands. Fix the ACLs (e.g., using 'put-bucket-acl --acl private')."
    ))
    
    messages = [prompt] + state.get("messages", [])
    plan = structured_llm.invoke(messages)
    
    print(f"   -> Drafted {len(plan.planned_actions)} actions.") #type: ignore
    
    # Update the State with the drafted plan
    return {
        "findings": plan.findings, #type: ignore
        "planned_actions": plan.planned_actions # type: ignore
    }