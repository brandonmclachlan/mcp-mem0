# main.py (Modified Snippets)
from mcp.server.fastmcp import FastMCP, Context
# ... other imports ...
from typing import Optional # Add Optional for the new parameter

# ... dataclass and lifespan ...

# Keep this, but it will be overridden by the tool parameter if provided
DEFAULT_USER_ID = "user"

# ... mcp initialization ...

@mcp.tool()
async def save_memory(ctx: Context, text: str, user_id: Optional[str] = None) -> str: # Add user_id parameter
    """Save information to long-term memory. (Keep description)

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        text: The content to store in memory, including any relevant details and context
        user_id: Optional identifier for the user/agent whose memory this belongs to.
    """
    # Use the provided user_id, otherwise fall back to default
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        messages = [{"role": "user", "content": text}]
        # Use target_user_id here
        mem0_client.add(messages, user_id=target_user_id)
        return f"Successfully saved memory for {target_user_id}: {text[:100]}..." if len(text) > 100 else f"Successfully saved memory for {target_user_id}: {text}"
    except Exception as e:
        return f"Error saving memory for {target_user_id}: {str(e)}"

@mcp.tool()
async def get_all_memories(ctx: Context, user_id: Optional[str] = None) -> str: # Add user_id parameter
    """Get all stored memories for the specified user/agent. (Update description)

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        user_id: Optional identifier for the user/agent whose memories to retrieve.

    Returns a JSON formatted list... (Keep description)
    """
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        # Use target_user_id here
        memories = mem0_client.get_all(user_id=target_user_id)
        # ... rest of the function ...
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error retrieving memories for {target_user_id}: {str(e)}"


@mcp.tool()
async def search_memories(ctx: Context, query: str, user_id: Optional[str] = None, limit: int = 3) -> str: # Add user_id parameter
    """Search memories for a specific user/agent using semantic search. (Update description)

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        query: Search query string describing what you're looking for. Can be natural language.
        user_id: Optional identifier for the user/agent whose memory to search.
        limit: Maximum number of results to return (default: 3)
    """
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
         # Use target_user_id here
        memories = mem0_client.search(query, user_id=target_user_id, limit=limit)
        # ... rest of the function ...
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error searching memories for {target_user_id}: {str(e)}"

# ... main async function ...
