import asyncio
import json
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def async_search_pubmed(query: str, max_results: int = 3) -> str:
    """
    Connects to the PubMed MCP server using stdio, calls the search tool, and returns the result.
    """
    server_params = StdioServerParameters(
        command="uvx",
        args=["--with", "fastmcp", "pubmedmcp@latest"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Fetch available tools to ensure it works
                tools = await session.list_tools()
                
                # pubmedmcp typically provides a tool named "search_pubmed" or similar.
                # If we don't know the exact tool name, we can try some standard ones.
                # Assuming the tool is named "search_abstracts".
                tool_name = "search_abstracts"
                
                # Some servers might name it differently, let's just attempt calling it
                result = await session.call_tool(
                    tool_name,
                    arguments={"request": {"term": query, "retmax": max_results}}
                )
                
                # Format the result by extracting text
                if result and result.content:
                    text_parts = [c.text for c in result.content if hasattr(c, 'text')]
                    return "\n\n".join(text_parts) if text_parts else str(result)
                return str(result)
                
    except Exception as e:
        return f"Error querying PubMed MCP Server: {str(e)}"

def search_pubmed_sync(query: str, max_results: int = 3) -> str:
    """
    Synchronous wrapper for searching PubMed via MCP.
    """
    try:
        # Check if there is an existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If running in a context where loop is already running (not typical for base Streamlit, but just in case)
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(async_search_pubmed(query, max_results))
        else:
            return loop.run_until_complete(async_search_pubmed(query, max_results))
    except RuntimeError:
        # Create a new event loop if none exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_search_pubmed(query, max_results))
