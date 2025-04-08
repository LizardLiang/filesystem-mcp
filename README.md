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
  - fd integration for file/folder discovery (despite the filename being fzf.py)
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
- Uses MCP (Master Control Program) tool protocol
- Communicates via stdin/stdout
- Designed for integration with AI agents and other tools

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

## Available Tools

SpiderFS MCP provides the following tools through the MCP protocol:

### `search_content`
Search for content in files using ripgrep or Python fallback.

Parameters:
- `path`: The file or directory path to search in
- `pattern`: The search pattern (supports regex)

### `fuzzy_file_search`
Search for files and directories using fuzzy matching.

Parameters:
- `pattern`: The search pattern (string)
- `root_path` (optional): Base directory to search from (default: system root)
- `max_results` (optional): Maximum number of results to return (default: 5)
- `include_dirs` (optional): Whether to include directories in search results (default: true)

### `read_file`
Read the contents of a file.

Parameters:
- `path`: The path to the file to read

### `write_file`
Write content to a file (replaces entire file).

Parameters:
- `path`: The path to the file to write
- `content`: The content to write to the file

### `edit_file`
Apply line-based edits to a file.

Parameters:
- `path`: The path to the file to edit
- `edits`: Array of edit objects with structure:
  - `line_start`: Starting line number (1-based)
  - `line_end`: Ending line number (inclusive)
  - `new_content`: New content to replace the specified lines

## Using the Fuzzy File Search

The fuzzy file search functionality allows for quick discovery of files and directories across the filesystem.

### Example Input:
```json
{
  "pattern": "config",
  "max_results": 10,
  "include_dirs": true
}
```

### Example Output:
```
C:\Users\username\AppData\Local\Programs\Python\config.py
D:\Projects\webapp\config\settings.js
D:\Projects\webapp\config
C:\ProgramData\config.ini
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