import pytest
from unittest.mock import patch, Mock, mock_open
from pydantic import AnyUrl

from rails_api_search.server import (
    search_api_docs,
    read_resource,
    call_tool,
    SearchParams
)

@pytest.fixture
def mock_html_content():
    return """
    <div>
        <h1>ActiveRecord Basics</h1>
        <p>Active Record is the M in MVC</p>
        <div id="methods">
            <h2>Methods</h2>
            <code>find(id)</code>
        </div>
    </div>
    """

@pytest.mark.asyncio
async def test_search_api_docs(mock_html_content):
    results = await search_api_docs(mock_html_content, "active record", 10)
    assert len(results["matches"]) > 0
    assert "Active Record" in results["matches"][0]["content"]

@pytest.mark.asyncio
async def test_read_resource():
    mock_content = "<html></html>"
    with patch('builtins.open', mock_open(read_data=mock_content)):
        uri = AnyUrl("rails-api://activerecord")
        result = await read_resource(uri)
        assert result == mock_content

@pytest.mark.asyncio
async def test_call_tool():
    with patch('rails_api_search.server.read_resource') as mock_read:
        mock_read.return_value = "<html><h1>Test</h1></html>"
        result = await call_tool("search", {"query": "test", "limit": 5})
        assert len(result) == 1
        assert isinstance(result[0].text, str)
