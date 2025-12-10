import asyncio
import os
import json
# Expecting 'mcp' package to be installed: pip install mcp
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError:
    print("Please install mcp SDK: pip install mcp")
    ClientSession = None
    sse_client = None

class MCPConnector:
    def __init__(self, server_url):
        self.server_url = server_url

    async def get_video_subtitles(self, video_url):
        if not sse_client:
            return "MCP SDK not installed."
        
        try:
            print(f"Connecting to MCP Server: {self.server_url}...")
            async with sse_client(url=self.server_url) as streams:
                async with ClientSession(streams.read, streams.write) as session:
                    # Initialize
                    await session.initialize()
                    
                    # Call Tool
                    # Tool name based on previous exploration: mcp_get_subtitles
                    # The argument name is likely 'url' based on description
                    result = await session.call_tool(
                        "mcp_get_subtitles", 
                        arguments={"url": video_url}
                    )
                    
                    # Parse result
                    # MCP returns a list of Content (TextContent usually)
                    output_text = ""
                    if result and result.content:
                        for content in result.content:
                            if hasattr(content, 'text'):
                                output_text += content.text
                    
                    return output_text

        except Exception as e:
            error_msg = f"MCP Error: {type(e).__name__}: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return error_msg

    async def get_video_comments(self, video_url):
        # Similar logic for comments
        if not sse_client:
            return []
        try:
            async with sse_client(url=self.server_url) as streams:
                async with ClientSession(streams.read, streams.write) as session:
                    await session.initialize()
                    result = await session.call_tool("mcp_get_comments", arguments={"url": video_url})
                    # Process result similar to above
                    return result
        except Exception as e:
            return str(e)
