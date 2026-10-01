import os
from pymongo import MongoClient
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from agent.state import SecOpsState
from agent.nodes import investigator_node, drafter_node, guardrail_node, execution_node

workflow = StateGraph(SecOpsState)

workflow.add_node("investigator", investigator_node)
workflow.add_node("drafter", drafter_node)
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("executor", execution_node)

def entry_gatekeeper(state: SecOpsState) -> str:
    """Checks if the incident in this thread has already been remediated."""
    if state.get("is_remediated") is True:
        print("[Memory Check] Incident already remediated in this thread. Skipping execution.")
        return END
    return "investigator"

workflow.add_conditional_edges(
    START,
    entry_gatekeeper,
    {
        "investigator": "investigator",
        END: END
    }
)
workflow.add_edge("investigator", "drafter")   # Pass findings to drafter
workflow.add_edge("drafter", "guardrail")      # Pass plan to security check
workflow.add_edge("guardrail", "executor")     # Pass safe plan to execution
workflow.add_edge("executor", END)             # Exit point

client = MongoClient(os.environ.get("MONGODB_URI"))
checkpointer = MongoDBSaver(client)

app = workflow.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("SecOps Graph compiled successfully!")