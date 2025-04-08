# SpiderFS MCP v0.2.0

SpiderFS MCP (Master Control Program) is a token-efficient file system server that provides search, read, and write operations with minimal data transfer.

## Features

### Search System
- **Content Search**:
  - Ripgrep integration for high-performance search
  - Python-based search fallback implementation
  - Support for regex patterns
  - Token-efficient result format

- **Fuzzy File Search** (New in v0.2.0):
  - fd/fzf integration for interactive file/folder discovery
  - Python-based file search fallback implementation
  - Returns top matches for AI agent selection (configurable)
  - Configurable search root (default: system root or all disks on Windows)
  - Support for both exact and fuzzy matching
  - Option to include/exclude directories in results

### Partial File Operations
- Read specific line ranges
- Read around matched content with configurable context
- Stream large files in chunks (line-based and byte-based)
- Efficient file writing with backup and atomic operations
- Support for different file encodings

### Server Interface
- FastAPI-based HTTP server
- JSON-based request/response format
- Endpoints for:
  - Content Search: Accept regex/string patterns, return matches with line numbers
  - Fuzzy File Search: Find files and directories matching patterns across the filesystem
  - Read: Accept line ranges or search context, return partial content
  - Write: Accept line-based edits and string replacement operations
  - Stream: Provide efficient streaming for large files

## Getting Started

### Prerequisites
- Python 3.10+
- Ripgrep (optional, for optimized content search)
- fd (optional, for optimized file search)
- pywin32 (automatically installed on Windows platforms)

### Installation
1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Run the server: `python -m spiderfs_mcp.server`

## API Endpoints

The API is available at `/api/v1/` with the following endpoints:

### Search
- `POST /api/v1/search/content`: Search for content in files
- `POST /api/v1/search/files`: Search for files/directories using fuzzy matching

### File Operations
- `POST /api/v1/file/read/range`: Read a specific range of lines from a file
- `POST /api/v1/file/read/context`: Read a line with context before and after
- `GET /api/v1/file/stream/lines/{file_path}`: Stream a file by lines
- `GET /api/v1/file/stream/bytes/{file_path}`: Stream a file by bytes
- `POST /api/v1/file/write/lines`: Apply line-based edits to a file
- `POST /api/v1/file/write/replace`: Replace strings in a file

## Using the Fuzzy File Search

The fuzzy file search functionality allows for quick discovery of files and directories across the filesystem.

### Parameters:
- `pattern`: The search pattern (string)
- `root_path` (optional): Base directory to search from (default: system root)
- `max_results` (optional): Maximum number of results to return (default: 5)
- `include_dirs` (optional): Whether to include directories in search results (default: true)

### Example Request:
```json
{
  "pattern": "config",
  "max_results": 10,
  "include_dirs": true
}
```

### Example Response:
```json
[
  "C:\\Users\\username\\AppData\\Local\\Programs\\Python\\config.py",
  "D:\\Projects\\webapp\\config\\settings.js",
  "D:\\Projects\\webapp\\config",
  "C:\\ProgramData\\config.ini"
]
```

## Enhanced Logging

SpiderFS MCP v0.2.0 includes improved logging capabilities:
- Detailed debug logs for search operations
- File operation tracing
- Error handling with stack traces
- Performance metrics

Logs are written to both console and `spiderfs_debug.log` file.

## Development

### Testing
Run tests with pytest:
```
pytest
```

For coverage report:
```
pytest --cov=spiderfs_mcp
```

### Windows-Specific Features
On Windows systems, fuzzy file search will automatically detect and search across all available drives when no specific root path is provided.