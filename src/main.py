# main-1.py (Modified for Bearer Authentication)

# --- Required Imports ---
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
from mem0 import Memory
import asyncio
import json
import os
from typing import Optional

# --- Imports needed for Authentication Middleware ---
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.routing import Mount
# --- End of added imports ---

from utils import get_mem0_client

load_dotenv()

# --- Define your secret token (read from environment) ---
# You MUST set this environment variable in Railway/Docker
EXPECTED_BEARER_TOKEN = os.getenv("MCP_SERVER_AUTH_TOKEN")
# --- End Authentication Variable ---

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
    (Original code - no changes needed here)
    """
    mem0_client = get_mem0_client()
    try:
        yield Mem0Context(mem0_client=mem0_client)
    finally:
        pass

# --- Define the Authentication Middleware (Bearer Token Check) ---
class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseCall
    ) -> Response:
        if not EXPECTED_BEARER_TOKEN:
            # If no token is set on the server, bypass auth (or raise error)
            # For production, you might want to deny access if the token isn't set
            print("Warning: MCP_SERVER_AUTH_TOKEN not set. Skipping auth check.")
            response = await call_next(request)
            return response

        # Apply authentication ONLY to the MCP SSE endpoint path
        if request.url.path == "/sse":
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                # Deny if Authorization header is missing
                return PlainTextResponse("Unauthorized: Missing Authorization header", status_code=401)

            # Check for 'Bearer ' prefix and extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                 return PlainTextResponse("Unauthorized: Invalid Authorization header format (Expected 'Bearer <token>')", status_code=401)

            token = parts[1] # The actual token sent by the client

            # Compare received token with the expected token
            if token != EXPECTED_BEERER_TOKEN:
                return PlainTextResponse("Forbidden: Invalid Bearer token", status_code=403)

        # If token is valid OR if the request path doesn't require auth, proceed
        response = await call_next(request)
        return response
# --- End Authentication Middleware ---


# Initialize FastMCP server (WITHOUT host/port, handled by Starlette/Uvicorn)
mcp = FastMCP(
    "mcp-mem0",
    description="MCP server for long term memory storage and retrieval with Mem0",
    lifespan=mem0_lifespan
)

# --- TOOL DEFINITIONS (Modified previously for user_id) ---
@mcp.tool()
async def save_memory(ctx: Context, text: str, user_id: Optional[str] = None) -> str:
    # (Keep the implementation from the previous 'minimally modified' version)
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        messages = [{"role": "user", "content": text}]
        mem0_client.add(messages, user_id=target_user_id)
        return f"Successfully saved memory for {target_user_id}: {text[:100]}..." if len(text) > 100 else f"Successfully saved memory for {target_user_id}: {text}"
    except Exception as e:
        return f"Error saving memory for {target_user_id}: {str(e)}"

@mcp.tool()
async def get_all_memories(ctx: Context, user_id: Optional[str] = None) -> str:
    # (Keep the implementation from the previous 'minimally modified' version)
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        memories = mem0_client.get_all(user_id=target_user_id)
        if isinstance(memories, dict) and "results" in memories:
            flattened_memories = [ memory.get("memory", "Memory content missing") for memory in memories["results"] ]
        elif isinstance(memories, list):
            flattened_memories = [ memory.get("memory", "Memory content missing") if isinstance(memory, dict) else str(memory) for memory in memories ]
        else:
            return json.dumps({"error": "Unexpected format received from mem0.get_all", "data": str(memories)})
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error retrieving memories for {target_user_id}: {str(e)}"

@mcp.tool()
async def search_memories(ctx: Context, query: str, user_id: Optional[str] = None, limit: int = 3) -> str:
    # (Keep the implementation from the previous 'minimally modified' version)
    target_user_id = user_id if user_id else DEFAULT_USER_ID
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        memories = mem0_client.search(query, user_id=target_user_id, limit=limit)
        if isinstance(memories, dict) and "results" in memories:
            flattened_memories = [ memory.get("memory", "Memory content missing") for memory in memories["results"] ]
        elif isinstance(memories, list):
             flattened_memories = [ memory.get("memory", "Memory content missing") if isinstance(memory, dict) else str(memory) for memory in memories ]
        else:
            return json.dumps({"error": "Unexpected format received from mem0.search", "data": str(memories)})
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error searching memories for {target_user_id}: {str(e)}"


# --- Create the Starlette app, add middleware, and mount the MCP SSE app ---
middleware = [
    Middleware(BearerAuthMiddleware) # Apply the Bearer Auth middleware
]
routes = [
    Mount("/sse", app=mcp.sse_app()) # Mount the FastMCP SSE handler at /sse
]
app = Starlette(routes=routes, middleware=middleware)
# --- End Starlette App Setup ---


# --- Modify main execution block to run the Starlette app ---
async def main():
    # Import uvicorn here or at the top
    try:
        import uvicorn
    except ImportError:
        print("Error: 'uvicorn' is not installed. Please install it: pip install uvicorn")
        return

    server_host = os.getenv("HOST", "0.0.0.0")
    # Read port from env, default to 8050 if not set or invalid
    try:
        server_port = int(os.getenv("PORT", "8050"))
    except ValueError:
        print("Warning: Invalid PORT environment variable. Defaulting to 8050.")
        server_port = 8050

    print(f"Starting server with Bearer Authentication on {server_host}:{server_port}")
    # Configure uvicorn to run the 'app' variable from this 'main.py' file
    config = uvicorn.Config("main:app", host=server_host, port=server_port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# --- Original main() logic commented out ---
# async def main_original():
#     transport = os.getenv("TRANSPORT", "sse")
#     if transport == 'sse':
#         await mcp.run_sse_async()
#     else:
#         await mcp.run_stdio_async()

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("DATABASE_URL"):
         print("Warning: DATABASE_URL environment variable not set.")
    if not EXPECTED_BEARER_TOKEN:
         print("Warning: MCP_SERVER_AUTH_TOKEN environment variable not set. Authentication will be bypassed.")

    asyncio.run(main())
