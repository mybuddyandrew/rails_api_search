import pytest
from unittest.mock import patch, Mock, mock_open
from pathlib import Path
from pydantic import AnyUrl

from rails_api_search.server import (
    search_api_docs,
    read_resource,
    call_tool,
    SearchParams,
    RAILS_API_SECTIONS
)

@pytest.fixture
def mock_html_content():
    return """
    <div>
        <h1>Rails API Documentation</h1>
        <section class="activerecord">
            <h1>ActiveRecord Basics</h1>
            <p>Active Record is the M in MVC</p>
            <div id="methods">
                <h2>Methods</h2>
                <code>find(id)</code>
            </div>
        </section>
        <section class="actionpack">
            <h1>Action Pack Overview</h1>
            <p>Action Pack handles routing and controllers</p>
        </section>
    </div>
    """

@pytest.mark.asyncio
async def test_search_api_docs_with_section(mock_html_content):
    results = await search_api_docs(mock_html_content, "active record", "activerecord", 10)
    assert len(results["matches"]) > 0
    assert "Active Record" in results["matches"][0]["content"]
    assert results["matches"][0]["section"] == "activerecord"

@pytest.mark.asyncio
async def test_search_api_docs_all_sections(mock_html_content):
    results = await search_api_docs(mock_html_content, "pack", None, 10)
    assert len(results["matches"]) > 0
    assert "Action Pack" in results["matches"][0]["content"]

@pytest.mark.asyncio
async def test_read_resource():
    mock_content = "<html></html>"
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_content)):
        uri = AnyUrl("rails-api://activerecord")
        result = await read_resource(uri)
        assert result == mock_content

@pytest.mark.asyncio
async def test_read_resource_all():
    mock_content = "<html></html>"
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_content)):
        uri = AnyUrl("rails-api://all")
        result = await read_resource(uri)
        assert result == mock_content

@pytest.mark.asyncio
async def test_call_tool():
    with patch('rails_api_search.server.read_resource') as mock_read:
        mock_read.return_value = "<html><h1>Test</h1></html>"
        result = await call_tool("search", {
            "query": "test",
            "section": "activerecord",
            "limit": 5
        })
        assert len(result) == 1
        assert isinstance(result[0].text, str)

@pytest.mark.asyncio
async def test_call_tool_all_sections():
    with patch('rails_api_search.server.read_resource') as mock_read:
        mock_read.return_value = "<html><h1>Test</h1></html>"
        result = await call_tool("search", {
            "query": "test",
            "limit": 5
        })
        assert len(result) == 1
        assert isinstance(result[0].text, str)

@pytest.mark.asyncio
async def test_search_api_docs_multiple_sections(mock_html_content):
    # Update the mock content to include multiple sections
    multi_section_content = """
    <div>
        <h1>Rails API Documentation</h1>
        <section class="actioncontroller">
            <h1>Action Controller Overview</h1>
            <p>Action Controller is the C in MVC</p>
        </section>
        <section class="activerecord">
            <h1>Active Record Basics</h1>
            <p>Active Record is the M in MVC</p>
        </section>
        <section class="actionview">
            <h1>Action View Overview</h1>
            <p>Action View is the V in MVC</p>
        </section>
    </div>
    """

    results = await search_api_docs(multi_section_content, "mvc", None, 10)
    assert len(results["matches"]) == 3
    sections = {match["section"] for match in results["matches"]}
    assert sections == {"actioncontroller", "activerecord", "actionview"}

@pytest.mark.asyncio
async def test_list_resources():
    resources = await list_resources()
    # Should have one resource for each section plus the "all" resource
    assert len(resources) == len(RAILS_API_SECTIONS) + 1

    # Verify the "all" resource is present
    all_resource = next(r for r in resources if r.uri.host == "all")
    assert all_resource.name == "Rails API Documentation - All"

    # Verify each section has a resource
    section_hosts = {r.uri.host for r in resources if r.uri.host != "all"}
    assert section_hosts == set(RAILS_API_SECTIONS.keys())
