# main.py (Minimally Modified for user_id)

from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
from mem0 import Memory
import asyncio
import json
import os
from typing import Optional # <<< ADDED IMPORT

from utils import get_mem0_client

load_dotenv()

# Default user ID for memory operations
DEFAULT_USER_ID = "user"

# Create a dataclass for our application context
@dataclass
class Mem0Context:
    """Context for the Mem0 MCP server."""
    mem0_client: Memory

@asynccontextmanager
async def mem0_lifespan(server: FastMCP) -> AsyncIterator[Mem0Context]:
    """
    Manages the Mem0 client lifecycle.

    Args:
        server: The FastMCP server instance

    Yields:
        Mem0Context: The context containing the Mem0 client
    """
    # Create and return the Memory client with the helper function in utils.py
    mem0_client = get_mem0_client()

    try:
        yield Mem0Context(mem0_client=mem0_client)
    finally:
        # No explicit cleanup needed for the Mem0 client
        pass

# Initialize FastMCP server with the Mem0 client as context
# --- THIS INITIALIZATION MUST HAPPEN BEFORE @mcp.tool DECORATORS ---
mcp = FastMCP(
    "mcp-mem0",
    description="MCP server for long term memory storage and retrieval with Mem0",
    lifespan=mem0_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8050")) # Ensure port is integer if reading from env
)

# --- TOOL DEFINITIONS USING THE 'mcp' VARIABLE DEFINED ABOVE ---

# Modified to accept user_id
@mcp.tool()
async def save_memory(ctx: Context, text: str, user_id: Optional[str] = None) -> str:
    """Save information to your long-term memory for a specific user/agent.

    This tool is designed to store any type of information that might be useful in the future.
    The content will be processed and indexed for later retrieval through semantic search.

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        text: The content to store in memory, including any relevant details and context
        user_id: Optional identifier for the user/agent whose memory this belongs to. Uses default if not provided.
    """
    # Use the provided user_id, otherwise fall back to default
    target_user_id = user_id if user_id else DEFAULT_USER_ID # <<< ADDED LOGIC
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        messages = [{"role": "user", "content": text}]
        # Use target_user_id here instead of DEFAULT_USER_ID
        mem0_client.add(messages, user_id=target_user_id) # <<< MODIFIED CALL
        # Updated success message for clarity
        return f"Successfully saved memory for {target_user_id}: {text[:100]}..." if len(text) > 100 else f"Successfully saved memory for {target_user_id}: {text}"
    except Exception as e:
        # Updated error message for clarity
        return f"Error saving memory for {target_user_id}: {str(e)}"

# Modified to accept user_id
@mcp.tool()
async def get_all_memories(ctx: Context, user_id: Optional[str] = None) -> str:
    """Get all stored memories for the specified user/agent.

    Call this tool when you need complete context of all previously memories for a specific user/agent.

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        user_id: Optional identifier for the user/agent whose memories to retrieve. Uses default if not provided.

    Returns a JSON formatted list of all stored memories, including when they were created
    and their content. Results are paginated with a default of 50 items per page.
    """
    # Use the provided user_id, otherwise fall back to default
    target_user_id = user_id if user_id else DEFAULT_USER_ID # <<< ADDED LOGIC
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
         # Use target_user_id here instead of DEFAULT_USER_ID
        memories = mem0_client.get_all(user_id=target_user_id) # <<< MODIFIED CALL
        if isinstance(memories, dict) and "results" in memories:
            # Make sure 'memory' key exists in each dict within results
            flattened_memories = [
                memory.get("memory", "Memory content missing")
                for memory in memories["results"]
            ]
        elif isinstance(memories, list): # Handle case where get_all might just return a list
             flattened_memories = [
                memory.get("memory", "Memory content missing") if isinstance(memory, dict) else str(memory)
                for memory in memories
            ]
        else:
            # Handle unexpected format
             return json.dumps({"error": "Unexpected format received from mem0.get_all", "data": str(memories)})

        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
         # Updated error message for clarity
        return f"Error retrieving memories for {target_user_id}: {str(e)}"

# Modified to accept user_id
@mcp.tool()
async def search_memories(ctx: Context, query: str, user_id: Optional[str] = None, limit: int = 3) -> str:
    """Search memories for a specific user/agent using semantic search.

    This tool should be called to find relevant information from memory for a specific user/agent. Results are ranked by relevance.
    Always search memories before making decisions to ensure you leverage existing knowledge for the right context.

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        query: Search query string describing what you're looking for. Can be natural language.
        user_id: Optional identifier for the user/agent whose memory to search. Uses default if not provided.
        limit: Maximum number of results to return (default: 3)
    """
     # Use the provided user_id, otherwise fall back to default
    target_user_id = user_id if user_id else DEFAULT_USER_ID # <<< ADDED LOGIC
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
         # Use target_user_id here instead of DEFAULT_USER_ID
        memories = mem0_client.search(query, user_id=target_user_id, limit=limit) # <<< MODIFIED CALL
        if isinstance(memories, dict) and "results" in memories:
             # Make sure 'memory' key exists in each dict within results
            flattened_memories = [
                memory.get("memory", "Memory content missing")
                for memory in memories["results"]
            ]
        elif isinstance(memories, list): # Handle case where search might just return a list
             flattened_memories = [
                memory.get("memory", "Memory content missing") if isinstance(memory, dict) else str(memory)
                for memory in memories
            ]
        else:
            # Handle unexpected format
             return json.dumps({"error": "Unexpected format received from mem0.search", "data": str(memories)})

        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
         # Updated error message for clarity
        return f"Error searching memories for {target_user_id}: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
