import logging
from pathlib import Path
from typing import Sequence
from enum import Enum
from mcp.server import Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    ClientCapabilities,
    TextContent,
    Tool,
    ListRootsResult,
    RootsCapability,
)
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FileSearch:
    path: str
    pattern: str


@dataclass
class FileRead:
    path: str


@dataclass
class FileWrite:
    path: str
    content: str


@dataclass
class FileEdit:
    path: str
    edits: List[dict]


class FileTools(str, Enum):
    SEARCH = "search_files"
    READ = "read_file"
    WRITE = "write_file"
    EDIT = "edit_file"


def search_files(path: str, pattern: str) -> str:
    from .search.ripgrep import RipgrepSearch

    result = RipgrepSearch().search(pattern, path)
    if result.error:
        return result.error
    return "\n".join(
        f"{m.path}:{m.line_number}:{m.line_content}" for m in result.matches
    )


def read_file(path: str) -> str:
    from .file.reader import FileReader

    return FileReader().read_file(path)


def write_file(path: str, content: str) -> str:
    from .file.writer import FileWriter

    result = FileWriter().replace_string(path, "", content)
    return (
        "Success"
        if result.success
        else (result.error if result.error else "No changes made")
    )


def edit_file(path: str, edits: List[dict]) -> str:
    from .file.writer import FileWriter, LineEdit

    line_edits = [
        LineEdit(e["line_start"], e["line_end"], e["new_content"]) for e in edits
    ]
    result = FileWriter().apply_line_edits(path, line_edits)
    return (
        f"Edited {result.changed_lines} lines"
        if result.success
        else (result.error if result.error else "No changes made")
    )


async def serve() -> None:
    logger = logging.getLogger(__name__)
    server = Server("mcp-filesystem")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name=FileTools.SEARCH,
                description="Search files using ripgrep",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "pattern": {"type": "string"},
                    },
                    "required": ["path", "pattern"],
                },
            ),
            Tool(
                name=FileTools.READ,
                description="Read file contents",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            ),
            Tool(
                name=FileTools.WRITE,
                description="Write file contents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name=FileTools.EDIT,
                description="Edit file lines",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "edits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "line_start": {"type": "integer"},
                                    "line_end": {"type": "integer"},
                                    "new_content": {"type": "string"},
                                },
                                "required": ["line_start", "line_end", "new_content"],
                            },
                        },
                    },
                    "required": ["path", "edits"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        try:
            match FileTools(name):
                case FileTools.SEARCH:
                    result = search_files(arguments["path"], arguments["pattern"])
                    return [TextContent(type="text", text=result)]

                case FileTools.READ:
                    result = read_file(arguments["path"])
                    return [TextContent(type="text", text=result)]

                case FileTools.WRITE:
                    result = write_file(arguments["path"], arguments["content"])
                    return [TextContent(type="text", text=result)]

                case FileTools.EDIT:
                    result = edit_file(arguments["path"], arguments["edits"])
                    return [TextContent(type="text", text=result)]

                case _:
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())

