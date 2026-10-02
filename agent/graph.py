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

mongo_uri = os.environ.get("MONGODB_URI")
if not mongo_uri:
    raise ValueError("MONGODB_URI environment variable is required.")

print("Establishing secure connection to MongoDB Atlas...")
client = MongoClient(mongo_uri)

try:
    # FAIL FAST: Force a ping to the server to guarantee we have write access
    # If your IP is not whitelisted in Atlas, this will immediately throw a loud error.
    client.admin.command('ping')
    print("MongoDB Atlas connection verified!")
except Exception as e:
    print(f"FATAL: Could not connect to MongoDB Atlas. Check your IP Whitelist and Credentials.\nError: {e}")
    exit(1)

checkpointer = MongoDBSaver(client, db_name="secops_agent_memory")

app = workflow.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("SecOps Graph compiled successfully!")