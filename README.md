# SpiderFS MCP v0.2.0

SpiderFS MCP (Master Control Program) is a token-efficient file system server that provides search, read, and write operations with minimal data transfer.

## Features

### Search System
- Ripgrep integration for high-performance search
- Python-based search fallback implementation
- Support for regex patterns
- Token-efficient result format

### Partial File Operations
- Read specific line ranges
- Read around matched content with configurable context
- Stream large files in chunks (line-based and byte-based)
- Efficient file writing with backup and atomic operations

### Server Interface
- FastAPI-based HTTP server
- JSON-based request/response format
- Endpoints for:
  - Search: Accept regex/string patterns, return matches with line numbers
  - Read: Accept line ranges or search context, return partial content
  - Write: Accept line-based edits and string replacement operations
  - Stream: Provide efficient streaming for large files

## Getting Started

### Prerequisites
- Python 3.12+
- Ripgrep (optional, for optimized search)

### Installation
1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Run the server: `python -m spiderfs_mcp.server`

## API Endpoints

The API is available at `/api/v1/` with the following endpoints:

### Search
- `POST /api/v1/search`: Search for content in files

### File Operations
- `POST /api/v1/file/read/range`: Read a specific range of lines from a file
- `POST /api/v1/file/read/context`: Read a line with context before and after
- `GET /api/v1/file/stream/lines/{file_path}`: Stream a file by lines
- `GET /api/v1/file/stream/bytes/{file_path}`: Stream a file by bytes
- `POST /api/v1/file/write/lines`: Apply line-based edits to a file
- `POST /api/v1/file/write/replace`: Replace strings in a file

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