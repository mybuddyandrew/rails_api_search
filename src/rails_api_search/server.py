import os
import json
import logging
from datetime import datetime
from collections.abc import Sequence
from typing import Any
from pathlib import Path

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

# Define available API sections
RAILS_API_SECTIONS = {
    # Framework Components
    "abstractcontroller": "AbstractController",
    "actioncable": "ActionCable",
    "actioncontroller": "ActionController",
    "actiondispatch": "ActionDispatch",
    "actionmailbox": "ActionMailbox",
    "actionmailer": "ActionMailer",
    "actiontext": "ActionText",
    "actionview": "ActionView",
    "activejob": "ActiveJob",
    "activemodel": "ActiveModel",
    "activerecord": "ActiveRecord",
    "activestorage": "ActiveStorage",
    "activesupport": "ActiveSupport",
    "arel": "Arel",
    "mail": "Mail",
    "mime": "Mime",
    "minitest": "Minitest",
    "rails": "Rails",

    # Core Extensions
    "array": "Array",
    "benchmark": "Benchmark",
    "bigdecimal": "BigDecimal",
    "class": "Class",
    "date": "Date",
    "dateandtime": "DateAndTime",
    "datetime": "DateTime",
    "delegator": "Delegator",
    "digest": "Digest",
    "erb": "ERB",
    "enumerable": "Enumerable",
    "exception": "Exception",
    "falseclass": "FalseClass",
    "file": "File",
    "float": "Float",
    "hash": "Hash",
    "io": "IO",
    "integer": "Integer",
    "kernel": "Kernel",
    "loaderror": "LoadError",
    "method": "Method",
    "module": "Module",
    "nameerror": "NameError",
    "nilclass": "NilClass",
    "numeric": "Numeric",
    "object": "Object",
    "pathname": "Pathname",
    "process": "Process",
    "range": "Range",
    "regexp": "Regexp",
    "securerandom": "SecureRandom",
    "singleton": "Singleton",
    "string": "String",
    "symbol": "Symbol",
    "thread": "Thread",
    "time": "Time",
    "trueclass": "TrueClass",
    "uri": "URI",
    "unboundmethod": "UnboundMethod",

    # Sub-sections
    "calculations": "DateAndTime::Calculations",
    "compatibility": "DateAndTime::Compatibility",
    "zones": "DateAndTime::Zones",
    "uuid": "Digest::UUID",
    "util": "ERB::Util",
    "concerning": "Module::Concerning",
    "backtrace": "Thread::Backtrace",
}

class SearchParams(BaseModel):
    query: str
    section: str | None = None  # Now optional - if None, search all sections
    limit: int = 10

class SearchResult(BaseModel):
    title: str
    content: str
    path: str
    section: str
    relevance: float = 1.0

def get_docs_path(section: str | None = None) -> Path:
    """Get path to documentation file for a section"""
    docs_dir = Path("docs")
    if section:
        return docs_dir / f"{section}.html"
    return docs_dir / "rails_api.html"

async def search_api_docs(content: str, query: str, section: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Search through Rails API documentation content"""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        results = []

        # Search through relevant HTML elements
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div', 'code']):
            text = element.get_text(strip=True)
            if query.lower() in text.lower():
                section_elem = element.find_parent(['section', 'div'])
                section_title = ""
                if section_elem:
                    headers = section_elem.find_all(['h1', 'h2', 'h3'])
                    if headers:
                        section_title = headers[0].text

                # Determine which section this content belongs to if not specified
                detected_section = section or "general"
                if not section:
                    # First try to match full nested sections (e.g., "DateAndTime::Calculations")
                    for sec_id, sec_name in RAILS_API_SECTIONS.items():
                        if "::" in sec_name:
                            parent, child = sec_name.split("::", 1)
                            if (parent.lower() in text.lower() and
                                child.lower() in text.lower()):
                                detected_section = sec_id
                                break

                    # If no nested section matched, try regular sections
                    if detected_section == "general":
                        for sec_id, sec_name in RAILS_API_SECTIONS.items():
                            if "::" not in sec_name and (
                                sec_id.lower() in text.lower() or
                                sec_name.lower() in text.lower()
                            ):
                                detected_section = sec_id
                                break

                result = SearchResult(
                    title=section_title or "Untitled Section",
                    content=text,
                    path=f"#{element.get('id', '')}" if element.get('id') else "",
                    section=detected_section,
                    relevance=len(query)/len(text) if text else 0
                )
                results.append(result.model_dump())

                if len(results) >= limit:
                    break

        return {
            "matches": sorted(results, key=lambda x: x['relevance'], reverse=True),
            "total": len(results),
            "query": query,
            "section": section,
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
    resources = []

    # Add general resource
    resources.append(
        Resource(
            uri=AnyUrl("rails-api://all"),
            name="Rails API Documentation - All",
            mimeType="text/html",
            description="Complete Ruby on Rails API documentation"
        )
    )

    # Add section-specific resources
    for section_id, section_name in RAILS_API_SECTIONS.items():
        resources.append(
            Resource(
                uri=AnyUrl(f"rails-api://{section_id}"),
                name=f"Rails API Documentation - {section_name}",
                mimeType="text/html",
                description=f"Ruby on Rails {section_name} API documentation"
            )
        )

    return resources

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read API documentation content"""
    try:
        section = uri.host if uri.host != "all" else None
        docs_path = get_docs_path(section)

        if not docs_path.exists():
            raise McpError(
                INVALID_PARAMS,
                f"Documentation not found for section: {section}"
            )

        with open(docs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except McpError:
        raise
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
        content = await read_resource(AnyUrl(f"rails-api://{params.section or 'all'}"))
        results = await search_api_docs(
            content,
            params.query,
            params.section,
            params.limit
        )

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
