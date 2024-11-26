import os
import json
import logging
from datetime import datetime
from collections.abc import Sequence
from typing import Any

from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    JSONRPCError as McpError,
    INTERNAL_ERROR,
    INVALID_PARAMS,
)
from pydantic import AnyUrl, BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rails-api-search")

class SearchParams(BaseModel):
    query: str
    section: str = "activerecord"
    limit: int = 10

class SearchResult(BaseModel):
    title: str
    content: str
    path: str
    relevance: float = 1.0

async def search_api_docs(content: str, query: str, limit: int = 10) -> dict[str, Any]:
    """Search through Rails API documentation content"""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        results = []

        # Search through relevant HTML elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div', 'code']):
            text = element.get_text(strip=True)
            if query.lower() in text.lower():
                section = element.find_parent(['section', 'div'])
                section_title = ""
                if section:
                    headers = section.find_all(['h1', 'h2', 'h3'])
                    if headers:
                        section_title = headers[0].text

                result = SearchResult(
                    title=section_title or "Untitled Section",
                    content=text,
                    path=f"#{element.get('id', '')}" if element.get('id') else "",
                    relevance=len(query)/len(text) if text else 0
                )
                results.append(result.model_dump())

                if len(results) >= limit:
                    break

        return {
            "matches": sorted(results, key=lambda x: x['relevance'], reverse=True),
            "total": len(results),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise McpError(
            INTERNAL_ERROR,
            f"Failed to search documentation: {str(e)}"
        )

app = Server("rails-api-search")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available API documentation resources"""
    return [
        Resource(
            uri=AnyUrl("rails-api://activerecord"),
            name="Rails API Documentation - ActiveRecord",
            mimeType="text/html",
            description="Ruby on Rails ActiveRecord API documentation"
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read API documentation content"""
    try:
        with open('rails_api.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise McpError(
            INTERNAL_ERROR,
            f"Failed to read documentation: {str(e)}"
        )

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available search tools"""
    return [
        Tool(
            name="search",
            description="Search the Rails API documentation",
            inputSchema=SearchParams.model_json_schema()
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for API documentation search"""
    if name != "search":
        raise McpError(
            INVALID_PARAMS,
            f"Unknown tool: {name}"
        )

    try:
        params = SearchParams(**arguments)
    except Exception as e:
        raise McpError(
            INVALID_PARAMS,
            f"Invalid search parameters: {str(e)}"
        )

    try:
        content = await read_resource(AnyUrl(f"rails-api://{params.section}"))
        results = await search_api_docs(content, params.query, params.limit)

        return [
            TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise McpError(
            INTERNAL_ERROR,
            f"Search operation failed: {str(e)}"
        )

async def main():
    """Main entry point for the server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
