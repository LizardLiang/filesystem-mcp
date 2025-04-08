import logging
import os
import sys
import traceback
from enum import Enum
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[logging.FileHandler("spiderfs_debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class ContentSearch:
    path: str
    pattern: str


@dataclass
class FuzzyFileSearch:
    pattern: str
    root_path: Optional[str] = None
    max_results: int = 5
    include_dirs: bool = True


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
    SEARCH = "search_content"
    FUZZY_SEARCH = "fuzzy_file_search"
    READ = "read_file"
    WRITE = "write_file"
    EDIT = "edit_file"


def fuzzy_file_search(
    pattern: str,
    root_path: Optional[str] = None,
    max_results: int = 5,
    include_dirs: bool = True,
) -> List[str]:
    """
    Search for files and/or directories using fuzzy matching
    Args:
        pattern: Search pattern
        root_path: Base directory to search from (None = system root)
        max_results: Maximum number of results to return
        include_dirs: Whether to include directories in search results
    Returns:
        List of matching file and/or directory paths
    """
    logger.debug(
        f"[FUZZY_SEARCH] Starting fuzzy_file_search with params: pattern='{pattern}', root_path='{root_path}', max_results={max_results}, include_dirs={include_dirs}"
    )

    # Log system information
    logger.debug(f"[FUZZY_SEARCH] System: {sys.platform}, Python: {sys.version}")
    logger.debug(f"[FUZZY_SEARCH] Working directory: {os.getcwd()}")

    try:
        from .search.fzf import FzfSearch

        logger.debug(f"[FUZZY_SEARCH] Successfully imported FzfSearch")

        search_instance = FzfSearch()
        logger.debug(
            f"[FUZZY_SEARCH] Created FzfSearch instance, fzf_available={search_instance.fd_available}"
        )

        results = search_instance.search(pattern, root_path, max_results, include_dirs)
        logger.debug(f"[FUZZY_SEARCH] Search completed, found {len(results)} results")

        # Log the results (but limit the output if there are many results)
        if results:
            result_preview = results[: min(3, len(results))]
            logger.debug(f"[FUZZY_SEARCH] First few results: {result_preview}")
            if len(results) > 3:
                logger.debug(f"[FUZZY_SEARCH] ... and {len(results) - 3} more results")
        else:
            logger.debug("[FUZZY_SEARCH] No results found")

        return results
    except Exception as e:
        logger.error(f"[FUZZY_SEARCH] Error in fuzzy_file_search: {str(e)}")
        logger.error(f"[FUZZY_SEARCH] Traceback: {traceback.format_exc()}")
        raise


def search_content(path: str, pattern: str) -> str:
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
    logger.info("[SERVER] Starting SpiderFsMcp server")
    server = Server("mcp-filesystem")
    logger.debug("[SERVER] Server instance created")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name=FileTools.SEARCH,
                description="Search file contents using ripgrep",
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
                name=FileTools.FUZZY_SEARCH,
                description="Fuzzy search for files and directories using fzf",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "root_path": {"type": "string", "default": None},
                        "max_results": {"type": "integer", "default": 5},
                        "include_dirs": {"type": "boolean", "default": True},
                    },
                    "required": ["pattern"],
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
        logger.debug(f"[CALL_TOOL] Tool called: {name}, arguments: {arguments}")
        try:
            match FileTools(name):
                case FileTools.SEARCH:
                    logger.debug(
                        f"[CALL_TOOL] Executing content search with path='{arguments['path']}', pattern='{arguments['pattern']}'"
                    )
                    result = search_content(arguments["path"], arguments["pattern"])
                    logger.debug(
                        f"[CALL_TOOL] Content search completed, result length: {len(result)}"
                    )
                    return [TextContent(type="text", text=result)]
                case FileTools.FUZZY_SEARCH:
                    pattern = arguments["pattern"]
                    root_path = arguments.get("root_path")
                    max_results = arguments.get("max_results", 5)
                    include_dirs = arguments.get("include_dirs", True)

                    logger.debug(
                        f"[CALL_TOOL] Executing fuzzy file search with pattern='{pattern}', root_path='{root_path}', max_results={max_results}, include_dirs={include_dirs}"
                    )

                    results = fuzzy_file_search(
                        pattern,
                        root_path,
                        max_results,
                        include_dirs,
                    )

                    logger.debug(
                        f"[CALL_TOOL] Fuzzy search completed, found {len(results)} results"
                    )
                    result_text = "\n".join(results)
                    logger.debug(
                        f"[CALL_TOOL] Returning results with length {len(result_text)}"
                    )

                    return [TextContent(type="text", text=result_text)]

                case FileTools.READ:
                    logger.debug(f"[CALL_TOOL] Reading file: {arguments['path']}")
                    result = read_file(arguments["path"])
                    logger.debug(
                        f"[CALL_TOOL] File read completed, content length: {len(result)}"
                    )
                    return [TextContent(type="text", text=result)]

                case FileTools.WRITE:
                    logger.debug(
                        f"[CALL_TOOL] Writing to file: {arguments['path']}, content length: {len(arguments['content'])}"
                    )
                    result = write_file(arguments["path"], arguments["content"])
                    logger.debug(f"[CALL_TOOL] File write completed, result: {result}")
                    return [TextContent(type="text", text=result)]

                case FileTools.EDIT:
                    logger.debug(
                        f"[CALL_TOOL] Editing file: {arguments['path']}, with {len(arguments['edits'])} edits"
                    )
                    result = edit_file(arguments["path"], arguments["edits"])
                    logger.debug(f"[CALL_TOOL] File edit completed, result: {result}")
                    return [TextContent(type="text", text=result)]

                case _:
                    logger.error(f"[CALL_TOOL] Unknown tool: {name}")
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            tb = traceback.format_exc()
            logger.error(
                f"[CALL_TOOL] Exception during tool execution: {error_msg}\n{tb}"
            )
            return [TextContent(type="text", text=error_msg)]

    logger.debug("[SERVER] Creating initialization options")
    options = server.create_initialization_options()
    logger.debug(f"[SERVER] Initialization options created: {options}")

    logger.info("[SERVER] Starting stdio server")
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("[SERVER] stdio server started, running server")
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
            logger.info("[SERVER] Server run completed")
    except Exception as e:
        logger.error(f"[SERVER] Fatal error in server: {str(e)}")
        logger.error(f"[SERVER] Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())
