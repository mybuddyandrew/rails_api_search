# Rails API Search MCP Server

An MCP server that provides search functionality for Rails API documentation, with a focus on ActiveRecord documentation.

## Components

### Resources

The server provides access to Rails API documentation through:
- Custom `rails-api://` URI scheme (e.g., `rails-api://activerecord`)
- Documentation content served as text/html mimetype
- Currently implements ActiveRecord documentation section

### Search Tool

The server implements a powerful search tool with the following capabilities:

#### Search Parameters
```json
{
  "query": "string",     // Required: Search term
  "section": "string",   // Optional: Documentation section (default: "activerecord")
  "limit": "integer"     // Optional: Max results to return (default: 10)
}
```

#### Search Results
Returns JSON formatted results including:
- Matched sections with titles and content
- Relevance scores
- Direct path links to sections
- Timestamp of search
- Total number of matches

Example response:
```json
{
  "matches": [
    {
      "title": "Section Title",
      "content": "Matched content...",
      "path": "#section-id",
      "relevance": 0.75
    }
  ],
  "total": 1,
  "query": "search term",
  "timestamp": "2024-03-21T10:00:00.000Z"
}
```

## Setup

### Prerequisites
- Python 3.12 or higher
- Rails API documentation file (`rails_api.html`) in the working directory

### Dependencies
```toml
dependencies = [
    "httpx",
    "beautifulsoup4",
    "python-dotenv",
    "mcp>=0.1.0",
]
```

### Installation

#### Claude Desktop Configuration

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development Configuration</summary>
  ```json
  "mcpServers": {
    "rails_api_search": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/andrewhodson/Desktop/rails_api_search",
        "run",
        "rails_api_search"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Production Configuration</summary>
  ```json
  "mcpServers": {
    "rails_api_search": {
      "command": "uvx",
      "args": [
        "rails_api_search"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

1. Sync dependencies:
```bash
uv sync
```

2. Build package:
```bash
uv build
```

3. Publish to PyPI:
```bash
uv publish
```

Required PyPI credentials:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Testing

Run tests with:
```bash
pytest
```

Test configuration is set up for:
- Strict asyncio mode
- Function-scoped test loops
- Test discovery in `tests/` directory

### Debugging

For debugging, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/andrewhodson/Desktop/rails_api_search run rails-api-search
```

The inspector provides a web interface for monitoring server communication and debugging issues.
