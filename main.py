import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from agent.graph import app
from agent.mcp_client import mcp_adapter

async def main():
    print("Starting SecOps Auto-Remediator...")
    
    await mcp_adapter.connect()
    
    try:
        initial_state = {
            "messages": [
                HumanMessage(content="Please secure our local AWS S3 environment. Find any misconfigured buckets, specifically looking for public-read ACLs, and fix them.")
            ]
        }
        
        # Thread ID to track the incident across multiple runs or nodes
        config = {"configurable": {"thread_id": "incident-003"}}
        
        async for output in app.astream(initial_state, config=config): # type: ignore
            for node_name, state_update in output.items():
                print(f"\n--- Finished Node: {node_name} ---\n")

        current_state = app.get_state(config) # type: ignore
        if current_state.next and "executor" in current_state.next:
            print("\n[HUMAN IN THE LOOP] The agent has drafted a remediation plan and is waiting for approval.")
            user_input = input("Type 'Y' to approve execution or 'N' to reject: ")

            if user_input.strip().upper() == 'Y':
                print("\nExecution approved. Resuming agent from MongoDB checkpoint...")
                # Resume the graph by passing 'None' as the input, using the exact same config
                async for output in app.astream(None, config=config): # type: ignore
                    for node_name, state_update in output.items():
                        print(f"\n--- Finished Node: {node_name} ---\n")
            else:
                print("\nExecution rejected. The agent will not proceed with remediation.")
        else:
            print("\nGraph reached END without requiring execution approval.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        await mcp_adapter.disconnect()
        print("Run complete.")

if __name__ == "__main__":
    asyncio.run(main())