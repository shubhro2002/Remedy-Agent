from langgraph.graph import StateGraph, START, END
from agent.state import SecOpsState
from agent.nodes import investigator_node, drafter_node, guardrail_node, execution_node

workflow = StateGraph(SecOpsState)

workflow.add_node("investigator", investigator_node)
workflow.add_node("drafter", drafter_node)
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("executor", execution_node)

workflow.add_edge(START, "investigator")       # Entry point
workflow.add_edge("investigator", "drafter")   # Pass findings to drafter
workflow.add_edge("drafter", "guardrail")      # Pass plan to security check
workflow.add_edge("guardrail", "executor")     # Pass safe plan to execution
workflow.add_edge("executor", END)             # Exit point

app = workflow.compile()

if __name__ == "__main__":
    print("SecOps Graph compiled successfully!")