from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from agent.llm import llm
from agent.state import SecOpsState
from agent.mcp_client import mcp_aws_tool

class RemediationPlan(BaseModel):
    findings: str = Field(description="Summary of the security vulnerabilities found.")
    planned_actions: List[str] = Field(description="List of exact AWS CLI commands to fix the issues.")

# Investigator Node
async def investigator_node(state: SecOpsState):
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

    # Bind the MCP tool
    llm_with_tools = llm.bind_tools([mcp_aws_tool])
    
    # Internal ReAct loop: Keep calling tools until the LLM stops asking for them
    while True:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)
        
        if not response.tool_calls:
            break # LLM has finished its investigation
            
        for tool_call in response.tool_calls:
            print(f"   -> Tool Call: {tool_call['args']}")
            
            # Execute the MCP tool and append the result to the conversation
            result = await mcp_aws_tool.ainvoke(tool_call["args"])
            
            # Show result for debugging
            print(f"   -> Result: {str(result)[:250]}") 
            
            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                
    return {"messages": messages}

# Drafter Node
async def drafter_node(state: SecOpsState):
    print("[Drafter] Drafting remediation plan...")
    
    # Bind the LLM to our Pydantic schema to force a structured JSON-like response
    structured_llm = llm.with_structured_output(RemediationPlan)
    
    prompt = SystemMessage(content=(
        "You are a SecOps Remediation Drafter. Review the conversation history. "
        "Draft the exact AWS CLI commands to remediate the vulnerability found by the investigator. "
        "CRITICAL RULES:\n"
        "1. Output ONLY individual, executable AWS CLI commands.\n"
        "2. DO NOT use bash loops (for/while), variables, or pseudo-code.\n"
        "3. DO NOT use destructive commands.\n"
        "4. Target ONLY the specific misconfigured bucket found by the investigator using 'put-bucket-acl'."
    ))
    
    messages = [prompt] + state.get("messages", [])
    plan = await structured_llm.ainvoke(messages)
    
    print(f"   -> Drafted {len(plan.planned_actions)} actions.") #type: ignore
    
    # Update the State with the drafted plan
    return {
        "findings": plan.findings, #type: ignore
        "planned_actions": plan.planned_actions # type: ignore
    }

# Guardrail Node
async def guardrail_node(state: SecOpsState):
    print("[Guardrail] Validating drafted actions...")
    
    planned_actions = state.get("planned_actions", [])
    approved_actions = []
    
    for cmd in planned_actions:
        # Defense-in-depth: Double-checking for destructive commands
        if " rm " in cmd or " rb " in cmd or "delete" in cmd:
            print(f"   -> BLOCKED by Graph Guardrail: {cmd}")
        else:
            print(f"   -> APPROVED: {cmd}")
            approved_actions.append(cmd)
            
    # Update the state with ONLY the approved actions
    return {"planned_actions": approved_actions}

# The Execution Node
async def execution_node(state: SecOpsState):
    print("[Executor] Executing approved actions...")
    
    actions = state.get("planned_actions", [])
    if not actions:
        print("   -> No valid actions to execute. Needs re-drafting.")
        return {"is_remediated": False}
        
    # TODO: In the next phase, wire this to the MCP Server to actually run the commands.
    # For now, simulate a successful execution to complete the state machine loop.
    for action in actions:
        print(f"   -> Executing via MCP: {action}")
        
    # Simulate success
    success_msg = AIMessage(content="Execution successful. The vulnerability has been remediated.")
    
    return {
        "messages": [success_msg],
        "is_remediated": True
    }