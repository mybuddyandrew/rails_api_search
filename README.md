# Rails API Search MCP Server

An MCP server that provides search functionality for Rails API documentation, supporting all major Rails framework components.

## Components

### Resources

The server provides access to Rails API documentation through:
- Custom `rails-api://` URI scheme
- Documentation content served as text/html mimetype
- Support for all major Rails framework sections and core extensions:

#### Framework Components
  - AbstractController
  - ActionCable
  - ActionController
  - ActionDispatch
  - ActionMailbox
  - ActionMailer
  - ActionText
  - ActionView
  - ActiveJob
  - ActiveModel
  - ActiveRecord
  - ActiveStorage
  - ActiveSupport
  - Arel
  - Mail
  - Mime
  - Minitest
  - Rails

#### Core Extensions
  - Array
  - Benchmark
  - BigDecimal
  - Class
  - Date
  - DateAndTime
    - Calculations
    - Compatibility
    - Zones
  - DateTime
  - Delegator
  - Digest
  - UUID
  - ERB
  - Util
  - Enumerable
  - Exception
  - FalseClass
  - File
  - Float
  - Hash
  - IO
  - Integer
  - Kernel
  - LoadError
  - Method
  - Module
  - Concerning
  - NameError
  - NilClass
  - Numeric
  - Object
  - Pathname
  - Process
  - Range
  - Regexp
  - SecureRandom
  - Singleton
  - String
  - Symbol
  - Thread
  - Backtrace
  - Time
  - TrueClass
  - URI
  - UnboundMethod

### Search Tool

The server implements a powerful search tool with the following capabilities:

#### Search Parameters
```json
{
  "query": "string",     // Required: Search term
  "section": "string",   // Optional: Documentation section (if omitted, searches all sections)
  "limit": "integer"     // Optional: Max results to return (default: 10)
}
```

#### Search Results
Returns JSON formatted results including:
- Matched sections with titles and content
- Section identification
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
      "section": "activerecord",
      "relevance": 0.75
    }
  ],
  "total": 1,
  "query": "search term",
  "section": "activerecord",
  "timestamp": "2024-03-21T10:00:00.000Z"
}
```

## Setup

### Prerequisites
- Python 3.12 or higher
- Rails API documentation files in the `docs/` directory:
  - `rails_api.html` (complete documentation)
  - Individual section files (e.g., `activerecord.html`, `actionview.html`, etc.)

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
{
  "mcpServers": {
    "rails_api_search": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/rails_api_search",
        "run",
        "rails_api_search"
      ]
    }
  }
}
```
</details>

<details>
  <summary>Production Configuration</summary>

```json
{
  "mcpServers": {
    "rails_api_search": {
      "command": "uvx",
      "args": [
        "rails_api_search"
      ]
    }
  }
}
```
</details>

## Development

### Project Structure
```
RAILS_API_SEARCH/
├── docs/
│   ├── rails_api.html           # Complete documentation
│   ├── activerecord.html        # ActiveRecord section
│   ├── actionview.html          # ActionView section
│   └── ...                      # Other section files
├── src/
│   └── rails_api_search/
│       ├── __init__.py
│       └── server.py
├── tests/
│   └── test_server.py
├── pyproject.toml
└── README.md
```

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

Test coverage includes:
- Section-specific searches
- Multi-section searches
- Resource listing
- Error handling
- File operations

### Debugging

For debugging, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/rails_api_search run rails-api-search
```

The inspector provides a web interface for:
- Monitoring server communication
- Testing search queries
- Verifying section detection
- Debugging issues

## Usage Examples

### Search Specific Section
```python
result = await call_tool("search", {
    "query": "migrations",
    "section": "activerecord",
    "limit": 5
})
```

### Search All Sections
```python
result = await call_tool("search", {
    "query": "mvc",
    "limit": 10
})
```

### List Available Sections
```python
resources = await list_resources()
```
