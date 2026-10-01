from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from langchain_core.tools import tool

class MCPAdapter:
    def __init__(self):
        # We tell the client exactly how to spin up our FastMCP server process
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_server/server.py"]
        )
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def connect(self):
        """Starts the subprocess and establishes the JSON-RPC session over stdio."""
        read, write = await self.exit_stack.enter_async_context(stdio_client(self.server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        print("MCP Client securely connected to FastMCP Server.")

    async def disconnect(self):
        """Safely shuts down the subprocess and cleans up pipes."""
        await self.exit_stack.aclose()
        print("MCP Client disconnected.")

    async def execute_command(self, command: str) -> str:
        """Sends the execution request over the MCP protocol."""
        if self.session is None:
            raise RuntimeError("MCP client is not connected")
        # We call the exact function name we registered in our FastMCP server
        session = self.session
        result = await session.call_tool(
            "execute_aws_cli",
            arguments={"command": command},
        )
        return result.content[0].text # type: ignore

# Create a global singleton adapter we can use across our LangGraph nodes
mcp_adapter = MCPAdapter()

# Wrap the MCP call in a standard LangChain tool so our AI can easily use it
@tool
async def mcp_aws_tool(command: str) -> str:
    """
    Executes an AWS CLI command against the local cloud environment.
    Always use this tool to investigate S3 buckets, ACLs, and IAM roles.
    """
    return await mcp_adapter.execute_command(command)