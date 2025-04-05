import sys
import os
import json
import logging

from pathlib import Path
from typing import Dict, Any, List
from spiderfs_mcp.search.ripgrep import RipgrepSearch
from spiderfs_mcp.file.reader import FileReader
from spiderfs_mcp.file.writer import FileWriter


# Configure logging to file for debugging
logging.basicConfig(
    level=logging.INFO,
    filename="spiderfs_mcp.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("spiderfs_mcp")

# Import SpiderFsMcp's existing functionality
logger.info("Successfully imported SpiderFsMcp modules")


class MCPAdapter:
    """Adapter for SpiderFsMcp to work with MCP protocol"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        logger.info(f"Initialized with base directory: {self.base_dir}")

        # Initialize SpiderFsMcp components if available
        self.ripgrep = RipgrepSearch()
        self.file_reader = FileReader()
        self.file_writer = FileWriter()

    def _resolve_path(self, path: str) -> str:
        """Resolve path relative to base directory"""
        path_obj = Path(path)

        # If path is absolute, check if it's within the base directory
        if path_obj.is_absolute():
            try:
                path_obj.relative_to(self.base_dir)
                return str(path_obj)
            except ValueError:
                # Path is outside base directory, use relative
                pass

        # Join with base directory
        return str(self.base_dir / path)

    def read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file's content"""
        try:
            path = self._resolve_path(params.get("path", ""))
            file_path = Path(path)

            if not file_path.exists():
                return {"error": f"File not found: {path}"}

            if file_path.is_dir():
                return {"error": f"Path is a directory, not a file: {path}"}

            # Use SpiderFsMcp's file reader if available
            content = self.file_reader.read_file(path)

            return {"content": content}
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return {"error": str(e)}

    def read_multiple_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read multiple files at once"""
        paths = params.get("paths", [])
        results = {}

        for path in paths:
            resolved_path = self._resolve_path(path)
            result = self.read_file({"path": resolved_path})
            if "content" in result:
                results[path] = {"content": result["content"]}
            else:
                results[path] = {"error": result.get("error", "Unknown error")}

        return results

    def write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            path = self._resolve_path(params.get("path", ""))
            content = params.get("content", "")

            # Use SpiderFsMcp's file writer replace_string method with empty old string to write the entire content
            path_obj = Path(path)
            if path_obj.exists():
                result = self.file_writer.replace_string(path, path_obj.read_text(), content)
            else:
                # For new files, create directory if needed
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                # Write content directly for new files
                path_obj.write_text(content)

            return {"success": True}
        except Exception as e:
            logger.error(f"Error writing file: {str(e)}")
            return {"error": str(e)}

    def list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files and directories in a path"""
        try:
            path = self._resolve_path(params.get("path", ""))
            dir_path = Path(path)

            if not dir_path.exists():
                return {"error": f"Directory not found: {path}"}

            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}

            entries = []
            for item in dir_path.iterdir():
                entry_type = "FILE" if item.is_file() else "DIR"
                entries.append(f"[{entry_type}] {item.name}")

            return {"entries": entries}
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return {"error": str(e)}

    def create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a directory"""
        try:
            path = self._resolve_path(params.get("path", ""))
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error creating directory: {str(e)}")
            return {"error": str(e)}

    def directory_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a recursive tree of files and directories"""
        try:
            path = self._resolve_path(params.get("path", ""))
            dir_path = Path(path)

            if not dir_path.exists():
                return {"error": f"Path not found: {path}"}

            def build_tree(current_path):
                """Recursively build tree structure"""
                item = {
                    "name": current_path.name,
                    "type": "file" if current_path.is_file() else "directory",
                }

                if current_path.is_dir():
                    children = []
                    try:
                        # Sort directories first, then files
                        sorted_paths = sorted(
                            current_path.iterdir(),
                            key=lambda p: (0 if p.is_file() else 1, p.name.lower()),
                        )
                        for child_path in sorted_paths:
                            # Skip hidden files and directories
                            if not child_path.name.startswith("."):
                                children.append(build_tree(child_path))
                    except PermissionError:
                        # Handle permission errors for restricted directories
                        pass

                    item["children"] = children

                return item

            result = build_tree(dir_path)
            return {"tree": result}
        except Exception as e:
            logger.error(f"Error getting directory tree: {str(e)}")
            return {"error": str(e)}

    def search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files matching a pattern"""
        try:
            path = self._resolve_path(params.get("path", ""))
            pattern = params.get("pattern", "")
            exclude_patterns = params.get("excludePatterns", [])

            # Use SpiderFsMcp's ripgrep search if available
            result = self.ripgrep.search(pattern, path, max_matches=1000)

            if result.error:
                # Fall back to Python search
                return self._search_files_by_name(path, pattern, exclude_patterns)

            # Format the results for MCP
            matches = [match.path for match in result.matches]
            return {"matches": matches}
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return {"error": str(e)}

    def _search_files_by_name(
        self, path: str, pattern: str, exclude_patterns: List[str] = []
    ) -> Dict[str, Any]:
        """Search files by name pattern using Python"""
        import fnmatch
        import re

        dir_path = Path(path)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": f"Invalid directory: {path}"}

        # Prepare exclude patterns as regex
        exclude_regexes = []
        if exclude_patterns:
            for ex_pattern in exclude_patterns:
                try:
                    exclude_regexes.append(re.compile(fnmatch.translate(ex_pattern)))
                except:
                    pass

        # Convert glob pattern to regex
        try:
            pattern_regex = re.compile(fnmatch.translate(pattern))
        except:
            return {"error": f"Invalid pattern: {pattern}"}

        matching_files = []

        for root, dirs, files in os.walk(dir_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(r.match(d) for r in exclude_regexes)]

            for filename in files:
                if pattern_regex.match(filename) and not any(
                    r.match(filename) for r in exclude_regexes
                ):
                    file_path = Path(root) / filename
                    matching_files.append(str(file_path))

        return {"matches": matching_files}

    def get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata about a file"""
        try:
            path = self._resolve_path(params.get("path", ""))
            file_path = Path(path)

            if not file_path.exists():
                return {"error": f"Path not found: {path}"}

            stat_info = file_path.stat()

            info = {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat_info.st_size,
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime,
            }

            return {"info": info}
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"error": str(e)}

    def list_allowed_directories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List allowed directories"""
        return {"directories": [str(self.base_dir)]}


def main():
    # Get base directory from command line args
    base_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    # Initialize MCP adapter
    adapter = MCPAdapter(base_dir)

    # Process stdin for commands
    for line in sys.stdin:
        try:
            request = json.loads(line)

            # Extract the function name and parameters
            func_name = request.get("function", "")
            params = request.get("params", {})
            request_id = request.get("id", "")

            # Map function names to methods
            func_map = {
                "read_file": adapter.read_file,
                "read_multiple_files": adapter.read_multiple_files,
                "write_file": adapter.write_file,
                "list_directory": adapter.list_directory,
                "create_directory": adapter.create_directory,
                "directory_tree": adapter.directory_tree,
                "search_files": adapter.search_files,
                "get_file_info": adapter.get_file_info,
                "list_allowed_directories": adapter.list_allowed_directories,
            }

            # Call the appropriate function
            if func_name in func_map:
                result = func_map[func_name](params)
            else:
                result = {"error": f"Unknown function: {func_name}"}

            # Construct the response
            response = {"id": request_id, "result": result}

            # Write the response to stdout
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {line}")
            # Send error response
            sys.stdout.write(
                json.dumps({"id": "", "result": {"error": "Invalid JSON request"}})
                + "\n"
            )
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            # Send error response
            sys.stdout.write(
                json.dumps(
                    {
                        "id": "",
                        "result": {"error": f"Error processing request: {str(e)}"},
                    }
                )
                + "\n"
            )
            sys.stdout.flush()


if __name__ == "__main__":
    main()
