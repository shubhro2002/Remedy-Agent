import asyncio
from langchain_core.messages import HumanMessage
from agent.graph import app
from agent.mcp_client import mcp_adapter

async def main():
    print(" Starting SecOps Auto-Remediator...")
    
    # 1. Start the FastMCP Server connection
    await mcp_adapter.connect()
    
    try:
        # 2. Give the agent its core mission
        initial_state = {
            "messages": [
                HumanMessage(content="Please secure our local AWS S3 environment. Find any misconfigured buckets, specifically looking for public-read ACLs, and fix them.")
            ]
        }
        
        # 3. Trigger and stream the LangGraph workflow
        async for output in app.astream(initial_state): # type: ignore
            # Print a visual divider after each node finishes
            for node_name, state_update in output.items():
                print(f"\n--- Finished Node: {node_name} ---\n")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        # 4. Ensure we gracefully close the MCP subprocess so we don't leak memory
        await mcp_adapter.disconnect()
        print(" Run complete.")

if __name__ == "__main__":
    asyncio.run(main())